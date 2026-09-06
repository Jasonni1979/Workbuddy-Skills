# 数据库方言与数据字典读取（db_dialects）

本文件给出各数据库的连接方式、所需 Python 驱动、以及 `crm_connect.py` 在"自动读取数据字典"
时执行的元数据查询。脚本统一通过 SQLAlchemy 的 `create_engine` 连接。

---

## 1. 连接串（SQLAlchemy URL 格式）

| 数据库 | dialect 参数 | 连接串模板 | 驱动 pip |
|---|---|---|---|
| MySQL / MariaDB | `mysql` | `mysql+pymysql://user:pass@host:3306/db` | `pymysql` |
| PostgreSQL | `postgresql` | `postgresql+psycopg2://user:pass@host:5432/db` | `psycopg2-binary` |
| SQL Server | `mssql` | `mssql+pyodbc://user:pass@host:1433/db?driver=ODBC+Driver+17+for+SQL+Server` | `pyodbc` |
| Oracle | `oracle` | `oracle+oracledb://user:pass@host:1521/?service_name=orcl` | `oracledb` |
| SQLite | `sqlite` | `sqlite:///absolute/path/to/file.db` | 内置 |

> 口令含特殊字符（@ : / %）时需 URL 编码（如 `@`→`%40`）。脚本命令行也接受单独参数传入，
> 避免把口令写进连接串。

---

## 2. 数据字典自动读取 SQL

`crm_connect.py --action dict` 按 dialect 选择下列查询，返回结构化字典。

### MySQL / MariaDB
```sql
SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
ORDER BY TABLE_NAME, ORDINAL_POSITION;
```

### PostgreSQL
```sql
SELECT c.table_name, c.column_name, c.data_type,
       c.is_nullable, pgd.description AS column_comment
FROM information_schema.columns c
LEFT JOIN pg_catalog.pg_statio_all_tables st ON c.table_name = st.relname
LEFT JOIN pg_catalog.pg_description pgd
       ON pgd.objoid = st.relid AND pgd.objsubid = c.ordinal_position
WHERE c.table_schema = 'public'
ORDER BY c.table_name, c.ordinal_position;
```

### SQL Server
```sql
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, '' AS COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_CATALOG = DB_NAME()
ORDER BY TABLE_NAME, ORDINAL_POSITION;
```

### Oracle
```sql
SELECT c.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE, c.NULLABLE,
       comm.COMMENTS AS COLUMN_COMMENT
FROM USER_TAB_COLUMNS c
LEFT JOIN USER_COL_COMMENTS comm
       ON comm.TABLE_NAME = c.TABLE_NAME AND comm.COLUMN_NAME = c.COLUMN_NAME
ORDER BY c.TABLE_NAME, c.COLUMN_ID;
```

### SQLite
```sql
-- 先取表清单，再逐表 PRAGMA
SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';
-- 对每张表：
PRAGMA table_info(table_name);
```

---

## 3. 连通性 / 权限探针

在正式抽取前，脚本执行：
- 通用：`SELECT 1`（验证连接与认证）
- 列清单：`SHOW TABLES` / `SELECT table_name FROM information_schema.tables ...`
仅当探针通过才继续，否则原样抛出错误请用户核对 host/port/user/password/白名单。

---

## 4. 常见错误排查

| 现象 | 可能原因 | 处理 |
|---|---|---|
| `ModuleNotFoundError: pymysql` | 未装驱动 | `pip install pymysql` |
| `Can't connect ... (61)` | host/port 错或防火墙 | 核对地址、确认数据库监听、放通白名单 |
| `Access denied for user` | 账号/口令/库名错 | 核对凭据、确认对该库有权限 |
| `Unknown database` | 库名错 | 用 `SHOW DATABASES` 核对 |
| SSL 报错 | 服务端要求 TLS | 在连接串加 `?ssl=true` 或 `?ssl_verify_cert=false`（视库方要求） |
| ODBC Driver 找不到 | 系统缺驱动 | 安装对应 ODBC Driver（如 MS ODBC 17/18） |
| Oracle `ORA-12514` | service_name 错 | 用正确 service_name / SID |

---

## 5. 手动字典格式（来源 2）

当用户手动提供时，请规整为以下任一形式供脚本消费：

**CSV**（表头：`table,column,type,comment`）：
```csv
orders,customer_id,BIGINT,客户ID
orders,order_date,DATE,下单日期
orders,amount,DECIMAL,订单金额
```

**JSON**（与脚本 `--action dict` 输出同构）：
```json
{"tables": [
  {"table": "orders",
   "columns": [{"name":"customer_id","type":"BIGINT","comment":"客户ID"}, ...]}
]}
```

脚本 `crm_analyze.py` 不直接依赖字典文件，字典仅用于第 4 步的字段映射确认；
真正分析只读取 `--data` 指向的 CSV/Excel 数据。
