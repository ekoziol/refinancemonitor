# Database Operations and Management

Comprehensive database management for: $ARGUMENTS

## Database Architecture Review

1. **Schema Analysis**:
   - Review dimensional model implementation
   - Validate fact and dimension table relationships
   - Check data types and constraints
   - Assess normalization vs denormalization decisions
   - Verify foreign key relationships

2. **Performance Assessment**:
   - Analyze query execution plans
   - Identify missing or unused indexes
   - Review table partitioning opportunities
   - Check for N+1 query problems
   - Assess connection pooling configuration

3. **Data Quality**:
   - Validate data integrity constraints
   - Check for orphaned records
   - Assess data freshness and staleness
   - Review data validation rules
   - Check for duplicate or inconsistent data

## Tortoise ORM Operations

### Model Management
```python
# Generate new migration
poetry run aerich init-db
poetry run aerich migrate

# Apply migrations
poetry run aerich upgrade

# Rollback migrations
poetry run aerich downgrade
```

### Query Optimization
```python
# Efficient queries with proper prefetching
from tortoise.query_utils import Prefetch

# Good: Use select_related for foreign keys
brands = await Brand.all().select_related("competitor_media_spend")

# Good: Use prefetch_related for reverse relationships
stores = await Store.all().prefetch_related("weekly_sales")

# Good: Use annotations for aggregations
sales_summary = await WeeklySales.annotate(
    total_sales=Sum("sales_lc")
).group_by("brand_id")
```

### Data Validation
```python
# Model-level validation
class FactWeeklySales(Model):
    sales_lc = fields.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    class Meta:
        table = "fct_weekly_sales"
        indexes = [
            ("brand_id", "date_id"),
            ("region_id", "date_id")
        ]
```

## Database Maintenance Tasks

### Performance Monitoring
```sql
-- Check slow queries
SELECT * FROM mysql.slow_log 
WHERE start_time > DATE_SUB(NOW(), INTERVAL 1 HOUR)
ORDER BY query_time DESC;

-- Analyze table statistics
ANALYZE TABLE fct_weekly_sales, dim_brand, dim_store;

-- Check index usage
SELECT 
    table_name,
    index_name,
    cardinality
FROM information_schema.statistics 
WHERE table_schema = 'artemis_mmm';
```

### Data Integrity Checks
```sql
-- Check for orphaned records
SELECT COUNT(*) FROM fct_weekly_sales f
LEFT JOIN dim_brand b ON f.brand_id = b.id
WHERE b.id IS NULL;

-- Validate data ranges
SELECT 
    MIN(sales_lc) as min_sales,
    MAX(sales_lc) as max_sales,
    COUNT(*) as total_records
FROM fct_weekly_sales 
WHERE date_id BETWEEN '2023-01-01' AND '2024-12-31';
```

### Index Optimization
```sql
-- Find missing indexes
SELECT 
    table_name,
    column_name,
    cardinality
FROM information_schema.columns c
WHERE table_schema = 'artemis_mmm'
AND NOT EXISTS (
    SELECT 1 FROM information_schema.statistics s
    WHERE s.table_name = c.table_name
    AND s.column_name = c.column_name
);

-- Create performance indexes for MMM queries
CREATE INDEX idx_weekly_sales_analysis 
ON fct_weekly_sales (brand_id, region_id, date_id);

CREATE INDEX idx_spend_channel_analysis 
ON fct_media_spend (channel_id, brand_id, date_id);
```

## Data Pipeline Operations

### ETL Process Management
```bash
# Run data pipeline
cd apps/backend
python -m src.shared.pipelines.runner

# Run specific transformation
python -m src.shared.pipelines.blob_to_db --table weekly_sales

# Validate data quality
python -m src.shared.utils.data_quality --check-all
```

### Data Seeding
```bash
# Seed dimension tables
python seed_forecast_data.py --dimensions-only

# Seed fact tables
python seed_forecast_data.py --facts-only

# Full data refresh
python seed_forecast_data.py --full-refresh
```

## MMM-Specific Database Operations

### Marketing Mix Model Data Prep
```python
# Prepare data for PyMC modeling
async def prepare_mmm_data(brand_id: int, start_date: date, end_date: date):
    # Sales data with media spend
    sales_data = await WeeklySales.filter(
        brand_id=brand_id,
        date__range=(start_date, end_date)
    ).select_related(
        "brand", "region", "date"
    ).prefetch_related(
        Prefetch(
            "media_spend",
            queryset=MediaSpend.filter(
                date__range=(start_date, end_date)
            ).select_related("channel")
        )
    )
    
    return sales_data
```

### Aggregation Queries for Analytics
```sql
-- Weekly sales by brand and channel spend
SELECT 
    b.brand_name,
    d.date,
    s.sales_lc,
    GROUP_CONCAT(
        CONCAT(mc.channel_name, ':', ms.spend_lc) 
        SEPARATOR '|'
    ) as channel_spend
FROM fct_weekly_sales s
JOIN dim_brand b ON s.brand_id = b.id
JOIN dim_date d ON s.date_id = d.id
LEFT JOIN fct_media_spend ms ON (
    s.brand_id = ms.brand_id AND 
    s.date_id = ms.date_id
)
LEFT JOIN dim_media_channel mc ON ms.channel_id = mc.id
WHERE b.id = ?
GROUP BY b.brand_name, d.date, s.sales_lc;
```

## Backup and Recovery

### Backup Strategy
```bash
# Daily backup
mysqldump --single-transaction --routines --triggers \
  artemis_mmm > backup_$(date +%Y%m%d).sql

# Automated backup with retention
mysqldump artemis_mmm | gzip > \
  /backups/artemis_mmm_$(date +%Y%m%d_%H%M%S).sql.gz

# Keep only last 30 days
find /backups -name "artemis_mmm_*.sql.gz" -mtime +30 -delete
```

### Recovery Testing
```bash
# Test restore to staging environment
mysql artemis_mmm_staging < backup_20241201.sql

# Validate restored data
python -m src.utils.data_validation --env staging
```

## Security and Compliance

### Database Security
- Enable SSL/TLS for all connections
- Use connection pooling with authentication
- Implement row-level security if needed
- Regular security updates and patches
- Monitor for unusual access patterns

### Data Privacy
- Implement data masking for non-production environments
- Regular audit of data access logs
- Ensure GDPR/CCPA compliance for customer data
- Secure backup encryption
- Document data retention policies

## Monitoring and Alerting

### Key Metrics
- Connection pool utilization
- Query response times
- Disk space usage
- Replication lag (if applicable)
- Error rates and deadlocks

### Alert Thresholds
- Slow query duration > 5 seconds
- Connection pool > 80% capacity
- Disk space > 85% full
- Replication lag > 60 seconds
- Error rate > 1% of total queries

## Database Checklist

### Performance
- [ ] All critical queries have proper indexes
- [ ] Query execution plans reviewed
- [ ] Connection pooling optimized
- [ ] Slow query monitoring enabled
- [ ] Regular statistics updates scheduled

### Security
- [ ] SSL/TLS enabled for connections
- [ ] User permissions follow least privilege
- [ ] Regular security updates applied
- [ ] Backup encryption enabled
- [ ] Access logging configured

### Reliability
- [ ] Automated backups running
- [ ] Recovery procedures tested
- [ ] Monitoring and alerting configured
- [ ] Data integrity checks scheduled
- [ ] Disaster recovery plan documented