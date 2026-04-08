package com.kakarote.finance.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class LocalSchemaInitializer implements InitializingBean {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Override
    public void afterPropertiesSet() {
        ensureClientCompanyTable();
        ensureAdminUserColumns();
        ensureAccountSetColumns();
        ensureUsernameUniqueIndex();
        seedPlatformAdmin();
    }

    private void ensureClientCompanyTable() {
        execute("CREATE TABLE IF NOT EXISTS wk_client_company (" +
                "client_id bigint NOT NULL," +
                "client_name varchar(255) NOT NULL," +
                "client_code varchar(100) DEFAULT NULL," +
                "contact_name varchar(100) DEFAULT NULL," +
                "contact_phone varchar(50) DEFAULT NULL," +
                "remark varchar(500) DEFAULT NULL," +
                "status int NOT NULL DEFAULT 1," +
                "create_user_id bigint DEFAULT NULL," +
                "create_time datetime DEFAULT NULL," +
                "update_user_id bigint DEFAULT NULL," +
                "update_time datetime DEFAULT NULL," +
                "PRIMARY KEY (client_id)," +
                "KEY idx_client_company_status(status)," +
                "KEY idx_client_company_name(client_name)" +
                ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");
    }

    private void ensureAdminUserColumns() {
        addColumnIfNotExists("wk_admin_user", "phone", "varchar(50) DEFAULT NULL");
        addColumnIfNotExists("wk_admin_user", "client_id", "bigint DEFAULT NULL");
        addColumnIfNotExists("wk_admin_user", "user_type", "varchar(50) DEFAULT 'client_user'");
        addColumnIfNotExists("wk_admin_user", "is_client_admin", "tinyint(1) NOT NULL DEFAULT 0");
    }

    private void ensureAccountSetColumns() {
        addColumnIfNotExists("wk_finance_account_set", "client_id", "bigint DEFAULT NULL");
        execute("CREATE INDEX IF NOT EXISTS idx_finance_account_set_client_id ON wk_finance_account_set(client_id)");
    }

    private void ensureUsernameUniqueIndex() {
        // MySQL does not support CREATE UNIQUE INDEX IF NOT EXISTS, so catch silently
        execute("CREATE UNIQUE INDEX uk_admin_user_username ON wk_admin_user(username)");
    }

    private void seedPlatformAdmin() {
        execute("UPDATE wk_admin_user SET user_type = 'platform_super_admin', is_admin = 1, is_client_admin = 0 WHERE user_id = 1");
    }

    /**
     * Add a column to a table only if it doesn't already exist (MySQL-compatible).
     */
    private void addColumnIfNotExists(String table, String column, String definition) {
        try {
            Integer count = jdbcTemplate.queryForObject(
                    "SELECT COUNT(*) FROM information_schema.columns " +
                    "WHERE table_schema = DATABASE() AND table_name = ? AND column_name = ?",
                    Integer.class, table, column);
            if (count != null && count == 0) {
                execute("ALTER TABLE " + table + " ADD COLUMN " + column + " " + definition);
            }
        } catch (Exception ex) {
            log.warn("Failed to ensure column {}.{}: {}", table, column, ex.getMessage());
        }
    }

    private void execute(String sql) {
        try {
            jdbcTemplate.execute(sql);
        } catch (Exception ex) {
            log.warn("schema init skipped for sql: {}", sql, ex.getMessage());
        }
    }
}
