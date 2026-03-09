## Summary
- Added external user role restrictions, personalized internal welcome messaging, database backup/restore scripts, and admin template import/export enhancements.    

## Highlights
- Restricted external users to `user` and `reviewer` roles only, with validation and UI error messaging for blocked role changes. 
- Added personalized `Welcome, [FIRST NAME]` messaging for internal users, with a generic welcome for external users. 
- Introduced database backup export and restore scripts with CSV manifest support and documented command-line options. 
- Enhanced admin template manager with JSON import/export, confirmation-based publishing, and success/error banners. 

## Breaking Changes
- External users can no longer be promoted to `admin` or `internal_readonly`; assignments are limited to `user` and `reviewer`. 

## Changes
### Added
- User Access Admin error banner for failed role updates. 
- External-role guard to limit assignments to `user` and `reviewer` only. 
- Welcome line below dev page titles showing `Welcome, [FIRST NAME]` for internal users. 
- Database backup export script to dump all schema tables to CSV with a manifest. 
- Database restore script to load CSV backups with optional truncate support. 
- Scripts README with usage examples and notes. 
- File-based JSON import and export in the dev template manager. 
- Post-import confirmation to publish the schema as a new active version. 
- Success and error banners for template operations. 

### Changed
- User Access Admin API validation now rejects external `admin` and `internal_readonly` promotions. 
- Dev pages now prefer the Entra display name for the first name and fall back to the email prefix when needed. 
- Template editor save flow is now shared for both manual saves and imported schema publishing. 
- Scripts README now documents all available command-line options. 

### Fixed
- Added UI error messaging to surface failed role update attempts in User Access Admin. 

## Upgrade / Migration Notes
- Review any workflows or expectations around external user role assignment, as external users are now restricted to `user` and `reviewer` roles only. 
- Database teams can begin using the new backup and restore scripts; refer to the README for supported options and usage examples. 
- Template admins can now import/export schemas via JSON and optionally publish imported schemas as new active versions. 

## Known Issues
- No known issues were listed in the provided change logs.

## Contributors
- Smiley Baltz