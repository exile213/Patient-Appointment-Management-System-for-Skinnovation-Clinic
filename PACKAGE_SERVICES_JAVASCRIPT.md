# Package Services - JavaScript Implementation Details

## Overview

The dynamic service row management is implemented using vanilla JavaScript (no jQuery). It works for both the "Add Package" form and individual "Edit Package" inline forms.

---

## Code Structure

### Main Initialization

```javascript
document.addEventListener('DOMContentLoaded', function() {
    // All initialization happens here
    // Ensures DOM is fully loaded before running
});
```

### Components

#### 1. Add Package Form Service Rows

**Container ID:** `addServicesContainer`

**HTML Structure:**
```html
<div id="addServicesContainer">
    <div class="service-row mb-2" data-row-index="0">
        <div class="input-group">
            <select class="form-control service-select" name="service_ids" required>
                <!-- service options -->
            </select>
            <button type="button" class="btn btn-outline-danger remove-service-btn" style="display: none;">
                <i class="fas fa-trash me-1"></i>Remove
            </button>
        </div>
    </div>
</div>

<button type="button" class="btn btn-outline-secondary mt-2" id="addServiceBtn">
    <i class="fas fa-plus me-2"></i>Add Another Service
</button>
```

**Functionality:**
- Initial single service dropdown displayed with remove button hidden
- Clicking "Add Another Service" clones the first row
- Remove buttons only show when multiple rows exist
- At least one service row always visible

#### 2. Edit Package Form Service Rows (Per Package)

**Container ID Pattern:** `editServicesContainer-{package_id}`

**HTML Structure:**
```html
<div id="editServicesContainer-{package_id}" class="edit-services-container">
    <!-- Pre-populated with existing package services -->
    <div class="service-row mb-2" data-row-index="0">
        <!-- service selection for existing service -->
    </div>
    <!-- Additional rows if package has multiple services -->
</div>

<button type="button" class="btn btn-outline-secondary mt-2 add-service-edit-btn" data-package-id="{package_id}">
    <i class="fas fa-plus me-2"></i>Add Another Service
</button>
```

**Functionality:**
- Each package has its own container with package ID
- Pre-populated with current services for that package
- Independent row management per package
- Remove buttons work within package scope

---

## Event Handlers

### Add Package Form Handler

```javascript
const addServiceBtn = document.getElementById('addServiceBtn');
const servicesContainer = document.getElementById('addServicesContainer');

if (addServiceBtn && servicesContainer) {
    addServiceBtn.addEventListener('click', function() {
        const rowCount = servicesContainer.querySelectorAll('.service-row').length;
        const firstRow = servicesContainer.querySelector('.service-row');
        const newRow = firstRow.cloneNode(true);
        
        // Reset select value to empty
        newRow.querySelector('select').value = '';
        newRow.setAttribute('data-row-index', rowCount);
        
        // Show remove button on new row
        newRow.querySelector('.remove-service-btn').style.display = 'inline-block';
        
        servicesContainer.appendChild(newRow);
        attachRemoveListener(newRow.querySelector('.remove-service-btn'));
        updateRemoveButtons();
    });
}
```

**Logic:**
1. Get current row count
2. Clone the first service row (template)
3. Reset the select dropdown to empty
4. Increment row index for tracking
5. Show remove button
6. Append to container
7. Attach event listener to remove button
8. Update visibility of all remove buttons

### Edit Package Form Handler

```javascript
document.querySelectorAll('.add-service-edit-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const packageId = this.getAttribute('data-package-id');
        const container = document.getElementById('editServicesContainer-' + packageId);
        // Similar logic to add form, but package-specific
    });
});
```

**Logic:**
- Get package ID from button data attribute
- Work within that package's container
- Same add/remove logic as main form

### Remove Button Handler

```javascript
function attachRemoveListener(btn) {
    btn.addEventListener('click', function() {
        const container = servicesContainer;
        if (container.querySelectorAll('.service-row').length > 1) {
            btn.closest('.service-row').remove();
            updateRemoveButtons();
        }
    });
}
```

**Logic:**
1. Check if more than 1 row exists
2. If yes, remove the clicked row
3. Update button visibility
4. If only 1 row remains, hide its remove button

---

## Helper Functions

### Update Remove Button Visibility

```javascript
function updateRemoveButtons() {
    const rows = servicesContainer.querySelectorAll('.service-row');
    rows.forEach(row => {
        const removeBtn = row.querySelector('.remove-service-btn');
        if (rows.length === 1) {
            removeBtn.style.display = 'none';
        } else {
            removeBtn.style.display = 'inline-block';
        }
    });
}
```

**Purpose:**
- Hide remove button when only 1 row exists (prevents accidental removal of last service)
- Show remove button when multiple rows exist
- Called after every add/remove operation

### Update Edit Package Remove Buttons

```javascript
function updateEditRemoveButtons(packageId) {
    const container = document.getElementById('editServicesContainer-' + packageId);
    const rows = container.querySelectorAll('.service-row');
    rows.forEach(row => {
        const removeBtn = row.querySelector('.remove-service-btn');
        if (rows.length === 1) {
            removeBtn.style.display = 'none';
        } else {
            removeBtn.style.display = 'inline-block';
        }
    });
}
```

**Purpose:**
- Same as main update function but for specific package containers
- Ensures each package maintains its own button state

---

## Data Handling

### Form Submission

When the form is submitted, the data is sent as:

```
service_ids[] = [service_id_1, service_id_2, service_id_3]
```

Multiple select elements with the same `name="service_ids"` are automatically collected into an array.

### Backend Processing

In the view (owner or staff):

```python
service_ids = request.POST.getlist('service_ids')
service_ids = [sid for sid in service_ids if sid]  # Filter empty values

if service_ids:
    services = Service.objects.filter(id__in=service_ids)
    for service in services:
        PackageService.objects.create(
            package=package,
            service=service
        )
```

---

## CSS Classes & Styling

### Service Row Structure

```html
<div class="service-row mb-2" data-row-index="0">
    <div class="input-group">
        <select class="form-control service-select">
            <!-- options -->
        </select>
        <button class="btn btn-outline-danger remove-service-btn">
            <!-- remove icon -->
        </button>
    </div>
</div>
```

**Classes:**
- `.service-row` - Container for each service selection row
- `.mb-2` - Bootstrap margin bottom (spacing)
- `.input-group` - Bootstrap input group for select + button combo
- `.form-control` - Bootstrap styling for select
- `.service-select` - Custom class for JavaScript targeting
- `.btn btn-outline-danger` - Bootstrap danger button outline
- `.remove-service-btn` - Custom class for remove button targeting

### Dynamic Show/Hide

```javascript
// Show element
element.style.display = 'inline-block';

// Hide element
element.style.display = 'none';
```

---

## Error Handling

### Missing Containers

```javascript
if (addServiceBtn && servicesContainer) {
    // Code only runs if both elements exist
}
```

Prevents JavaScript errors if elements don't exist (e.g., on different pages).

### Duplicate Event Listeners

```javascript
document.querySelectorAll('.add-service-edit-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        // Each button gets its own listener
    });
});
```

Uses forEach to attach separate listeners to each edit button, preventing conflicts.

---

## Template Integration

### In Base Template
The JavaScript is included directly in the template within a `<script>` tag at the bottom of the page.

### Execution Flow

1. Page loads
2. DOM fully renders
3. `DOMContentLoaded` fires
4. JavaScript finds elements and attaches listeners
5. User interactions trigger event handlers
6. DOM is dynamically updated
7. Form submits with service selections

---

## Browser Compatibility

**Supported in:**
- Chrome 42+
- Firefox 37+
- Safari 10+
- Edge 12+
- IE 11 (with polyfills - not tested)

**Features Used:**
- `document.querySelectorAll()` - IE 8+
- `element.cloneNode()` - IE 6+
- `element.closest()` - IE not supported, but not used in current code
- `addEventListener()` - IE 9+
- Template literals - not used, using string concatenation

---

## Performance Considerations

1. **Event Delegation:** Individual listeners on each button (not optimal but fine for small numbers)
2. **DOM Cloning:** Fast operation, fine for up to 10-20 rows
3. **No Library:** Vanilla JS, no dependencies
4. **Minimal Reflows:** Batch DOM updates when possible

---

## Debugging Tips

### Check Element Exists
```javascript
console.log(document.getElementById('addServicesContainer'));
```

### Check Event Listener Attached
```javascript
// Open DevTools → Elements → Right-click element → Inspect
// Check Event Listeners panel
```

### Monitor Service IDs on Submit
```javascript
// In browser console before submitting form:
const formData = new FormData(document.querySelector('#addPackageForm'));
console.log(formData.getAll('service_ids'));
```

### Verify Row Count
```javascript
document.querySelectorAll('#addServicesContainer .service-row').length
```

---

## Testing Scenarios

| Scenario | Expected Result |
|----------|-----------------|
| Add package, add service | Service row appears with remove button hidden |
| Add second service | Remove buttons appear on both rows |
| Remove first service | Remaining service has remove button hidden |
| Add three services, remove middle one | Middle row deleted, other rows remain |
| Edit package with services | Existing services pre-populated, can add/remove |
| Switch service dropdown | New service selected in that row |

---

## Future Enhancements

1. **Drag & Drop Reordering:** Reorder services by dragging
2. **Service Details Preview:** Show service price/duration on hover
3. **Validation:** Prevent duplicate services in same package
4. **Batch Operations:** Add/remove all services at once
5. **Search:** Filter services in dropdown while typing

---

## Code Maintenance

When modifying:
1. Keep vanilla JS (no jQuery)
2. Maintain consistent naming: `.service-row`, `.remove-service-btn`, `service_ids`
3. Update both main form and edit form handlers together
4. Test with 1 service, 3 services, and 10+ services
5. Verify form submission sends correct service_ids array
