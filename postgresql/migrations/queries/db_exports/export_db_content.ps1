$password = "postgreSQLPassword%21%40"
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = "C:/Users/baltzjo/Documents/SPFx-Local/vp-qc-checklist-app/.admin/queries/db_exports"

# Get table list (schema-qualified)
$tables = psql "postgresql://postgres:$password@localhost:5432/postgres" -At `
  -c "SELECT quote_ident(schemaname)||'.'||quote_ident(tablename)
      FROM pg_tables
      WHERE schemaname = 'qc_coversheet'
      ORDER BY tablename;"

foreach ($t in $tables) {
  $name = ($t -split '\.')[1].Trim('"')   # just table name for filename
  $file = "$outDir/${ts}_$name.csv"
  psql "postgresql://postgres:$password@localhost:5432/postgres" `
    -c "\copy $t TO '$file' CSV HEADER"
  Write-Host "Exported $t -> $file"
}