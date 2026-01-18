# Admin Soft Delete Feature - Testing Checklist

## Overview
This document provides a comprehensive testing checklist for the admin-only soft delete feature for comments.

## Prerequisites
1. Database has been initialized with new schema (columns added automatically on first run)
2. At least one user account exists with `is_admin=True` (set manually in database)
3. Test data: Some games with comments and requests board comments exist

## Setting Up Admin User (Manual)
To set a user as admin, use the following SQL command in your database:

```sql
UPDATE user SET is_admin = 1 WHERE username = 'your_admin_username';
```

Or using Python shell:
```python
from app import app, db
from models import User

with app.app_context():
    user = User.query.filter_by(username='your_admin_username').first()
    user.is_admin = True
    db.session.commit()
```

## Test Cases

### 1. Admin Authorization Tests

#### 1.1 Admin Login
- [ ] Admin user can log in successfully
- [ ] Admin sees "Show Deleted (Admin)" checkbox on game detail pages
- [ ] Admin sees "Show Deleted (Admin)" checkbox on requests board
- [ ] Admin sees "Delete" buttons next to all comments (both game and requests)

#### 1.2 Non-Admin User
- [ ] Regular user does NOT see "Show Deleted (Admin)" checkbox
- [ ] Regular user does NOT see "Delete" buttons
- [ ] Regular user cannot access `/comment/<id>/delete` route (should get 403 error)
- [ ] Regular user cannot access `/comment/<id>/restore` route (should get 403 error)

#### 1.3 Guest/Anonymous User
- [ ] Anonymous user does NOT see admin controls
- [ ] Anonymous user redirected to login when trying to access delete routes

### 2. Delete Functionality Tests

#### 2.1 Deleting Game Comments
- [ ] Admin can click "Delete" button next to a game comment
- [ ] Delete form appears with optional reason field
- [ ] Admin can cancel deletion (form hides)
- [ ] Admin can confirm deletion without reason
- [ ] Admin can confirm deletion with reason
- [ ] After deletion, comment disappears from view (unless show_deleted is enabled)
- [ ] Success message appears: "Comment deleted successfully."
- [ ] Page redirects back to the same game detail page

#### 2.2 Deleting Nested Replies
- [ ] Admin can delete a reply to a comment
- [ ] Deleting a parent comment does NOT delete its replies
- [ ] Replies to deleted comments remain visible (if not themselves deleted)
- [ ] Thread structure is preserved

#### 2.3 Deleting Requests Board Comments
- [ ] Admin can delete top-level requests board posts
- [ ] Admin can delete replies on requests board
- [ ] After deletion, page redirects back to requests board
- [ ] Success message appears

#### 2.4 Deleting Guest Comments
- [ ] Admin can delete comments posted by guests
- [ ] Guest comments are handled the same as authenticated user comments

### 3. Restore Functionality Tests

#### 3.1 Restoring Game Comments
- [ ] Admin enables "Show Deleted (Admin)" checkbox
- [ ] Deleted comments appear with red border and background
- [ ] Deleted comments show "[DELETED]" label
- [ ] Deleted content is replaced with "[Content deleted]" or "[Content deleted: reason]"
- [ ] "Restore" button appears for deleted comments (green text)
- [ ] Clicking "Restore" restores the comment
- [ ] Restored comment appears normally again
- [ ] Success message: "Comment restored successfully."

#### 3.2 Restoring Requests Board Comments
- [ ] Same tests as 3.1 but on requests board

### 4. Display Behavior Tests

#### 4.1 Default View (show_deleted=false)
- [ ] Non-admin users: deleted comments are completely hidden
- [ ] Admin users: deleted comments are hidden by default
- [ ] Comment count appears correct (excludes deleted)
- [ ] Thread structure is maintained when parent is deleted

#### 4.2 Admin View (show_deleted=true)
- [ ] Only available to admin users
- [ ] Deleted comments appear with distinct styling:
  - Red left border (#ff6b6b)
  - Pink background (#ffe0e0)
  - "[DELETED]" label in red
- [ ] Content replaced with placeholder text
- [ ] Delete reason shown if provided
- [ ] "Reply" button hidden on deleted comments
- [ ] Author tag change dropdown hidden on deleted comments (game detail only)

### 5. Integration Tests

#### 5.1 Interaction with Hidden Tag Feature
- [ ] Admin can delete a comment that has "hidden" tag
- [ ] Hidden comments can be restored from soft delete
- [ ] Auto-restore 7-day rule still works for hidden tags
- [ ] Tag change functionality disabled for deleted comments

#### 5.2 Interaction with Author Controls
- [ ] Game authors can still change tags on their non-deleted comments
- [ ] Game authors cannot change tags on deleted comments
- [ ] Deleting doesn't affect game author's ability to edit/delete games

#### 5.3 Tag Filtering
- [ ] Tag filters work correctly with deleted comments hidden
- [ ] Tag filters work correctly with deleted comments shown
- [ ] Filtering by tag doesn't show deleted comments (unless show_deleted=true)

### 6. Database Tests

#### 6.1 Soft Delete Persistence
- [ ] Deleted comments remain in database (not hard deleted)
- [ ] `is_deleted` field set to True
- [ ] `deleted_at` timestamp recorded
- [ ] `deleted_by_user_id` references admin user
- [ ] `delete_reason` stored correctly (or NULL if not provided)

#### 6.2 Restore Clears Fields
- [ ] After restore, `is_deleted` = False
- [ ] After restore, `deleted_at` = NULL
- [ ] After restore, `deleted_by_user_id` = NULL
- [ ] After restore, `delete_reason` = NULL
- [ ] Original content and other fields unchanged

### 7. Edge Cases

#### 7.1 Multiple Actions
- [ ] Admin can delete multiple comments in sequence
- [ ] Admin can delete and restore the same comment multiple times
- [ ] Deleting a comment with many nested replies works correctly

#### 7.2 URL Parameters
- [ ] `show_deleted=true` parameter persists correctly in URLs
- [ ] Tag filter + show_deleted both work together
- [ ] show_hidden + show_deleted both work together (game detail only)

#### 7.3 Security
- [ ] Non-admin cannot access delete route by crafting URL
- [ ] Non-admin cannot access restore route by crafting URL
- [ ] CSRF protection works on delete forms
- [ ] CSRF protection works on restore forms

### 8. UI/UX Tests

#### 8.1 Visual Feedback
- [ ] Delete button clearly labeled and red colored
- [ ] Restore button clearly labeled and green colored
- [ ] Deleted comment styling is distinct and obvious
- [ ] Delete confirmation form is user-friendly
- [ ] Success messages appear and are clear

#### 8.2 Navigation
- [ ] All redirects work correctly
- [ ] User stays on same page after delete/restore
- [ ] Scroll position is reasonable after redirect

## Post-Testing Verification

After completing all tests:

1. [ ] Check database for orphaned data
2. [ ] Verify no JavaScript console errors
3. [ ] Test on both game detail and requests board pages
4. [ ] Confirm existing features (comments, replies, tags) still work
5. [ ] Review code for any TODO comments or debugging statements

## Known Limitations

1. **Thread Structure**: When a comment is deleted, its replies remain visible. The deleted comment shows as a placeholder.
2. **Admin Promotion**: No UI for promoting users to admin - must be done manually in database.
3. **Audit Trail**: Deletion/restoration actions are not logged in a separate audit table (only soft delete fields tracked).

## Testing Summary

| Category | Tests Passed | Tests Failed | Notes |
|----------|--------------|--------------|-------|
| Admin Authorization | | | |
| Delete Functionality | | | |
| Restore Functionality | | | |
| Display Behavior | | | |
| Integration Tests | | | |
| Database Tests | | | |
| Edge Cases | | | |
| UI/UX Tests | | | |

---

**Tested by:** _______________
**Date:** _______________
**Environment:** Development / Staging / Production
**Notes:**
