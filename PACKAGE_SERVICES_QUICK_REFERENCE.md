# Quick Reference: Package Services Implementation

## What Changed?

Packages now support bundling multiple services. Staff/owners can select services when creating or editing packages.

## How to Use

### Adding a Package with Services

1. **Go to:** Owner → Manage Packages (or Staff → Manage Packages)
2. **Fill in package details:**

   - Package Name (e.g., "3 + 1 Diamond Peel")
   - Price (₱)
   - Sessions (number of patient visits)
   - Duration (days)
   - Grace Period (optional)
   - Description (optional)

3. **Select Services:**

   - Choose first service from dropdown (required)
   - Click "Add Another Service" to add more services
   - Each service can be removed via the "Remove" button
   - At least 1 service is required

4. **Submit:** Click "Add Package" button

### Editing an Existing Package

1. **Click Edit** on the package row
2. **Modify any fields** including services
3. **Manage services:**
   - Add new services with "Add Another Service" button
   - Remove existing services with the "Remove" button
   - Pre-filled with current package services
4. **Save Changes**

### Viewing Package Services

**In List View:**

- Services display as blue badges under "Services" column
- Example: `Diamond Peel | IPL Face | Cavitation`

**In Admin:**

- Django admin shows service count in PackageAdmin list
- Click into package to add/remove services inline
- PackageService admin shows all service-package relationships

## Key Features

| Feature                 | Details                                           |
| ----------------------- | ------------------------------------------------- |
| **Dynamic Rows**        | Add/remove service dropdowns on-the-fly           |
| **Validation**          | At least one service required per package         |
| **Data Integrity**      | No duplicate service assignments allowed          |
| **Backward Compatible** | Existing packages preserved without breaking      |
| **Auto-Migration**      | Existing packages auto-linked to services by name |

## Database Changes

### New Model: `PackageService`

- Through model to track package-service relationships
- Unique constraint: no duplicates

### Updated Model: `Package`

- New field: `services` (ManyToMany to Service)
- Blank=True to support packages without services during transition

## Migration Commands

```bash
# Apply migrations
python manage.py migrate packages

# Check migration status
python manage.py showmigrations packages

# Revert migrations (if needed)
python manage.py migrate packages 0003
```

## How Services Are Auto-Linked

Data migration `0005_auto_link_packages_to_services` automatically links existing packages:

1. Removes "3 + 1 " prefix from package name
2. Matches against service names (case-insensitive)
3. Logs success/failure for each package

Example:

- Package: "3 + 1 Diamond Peel"
- Becomes: "Diamond Peel"
- Links to: Service named "Diamond Peel"

## Configuration Notes

### Sessions Field

- Represents number of patient **visits**
- Manually configured per package
- Independent from service count
- Examples:
  - "3 + 1 Diamond Peel" = 4 sessions (patient comes 4 times)
  - "3 + 1 IPL Face" = 4 sessions (patient comes 4 times)

### Services in Package

- Multiple different services can be bundled
- Each service performed on one or more of the patient visits
- No automatic session calculation from services
- Manually configured per package

### Pricing

- Package price is manually set
- Not auto-calculated from services
- Allows for flexible discount strategies

## Troubleshooting

**Problem:** Existing packages don't show services after migration

- **Solution:** Check migration log, manually assign services in admin

**Problem:** Can't remove last service from package

- **Solution:** This is by design - packages must have at least 1 service

**Problem:** Service dropdown shows archived services

- **Solution:** Only non-archived services appear in dropdowns

**Problem:** Duplicate service assignments attempt

- **Solution:** Database prevents duplicates with unique constraint

## Testing Checklist

- [ ] Add new package with 1 service
- [ ] Add new package with 3 services
- [ ] Edit package and add more services
- [ ] Edit package and remove services
- [ ] Verify services display in package list
- [ ] Check admin inline service management
- [ ] Verify existing packages have services linked
- [ ] Create package appointment and check services in appointment detail

## File Locations

| Component  | File                                       |
| ---------- | ------------------------------------------ |
| Models     | `packages/models.py`                       |
| Forms      | `packages/forms.py`                        |
| Owner View | `owner/views.py` (line 1285+)              |
| Staff View | `appointments/admin_views.py` (line 2145+) |
| Template   | `templates/owner/manage_packages.html`     |
| Admin      | `packages/admin.py`                        |
| Migrations | `packages/migrations/000X_*.py`            |

## Support

For issues or questions, refer to:

- Full implementation summary: `PACKAGE_SERVICES_IMPLEMENTATION.md`
- Django admin documentation
- Package models documentation in code comments
