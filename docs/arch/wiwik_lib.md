# wiwik_lib

## Models

wiwik_lib django-app introduces some helper models:

- `Flag` - Flag a model that inherits from `Flaggable` model.
- `EditedResource` - Mark that a model that inherits from `Editable` is currently being edited.
  This can serve as a lock on the model preventing multiple simultaneous edits.

## Views

### `view_flag_model`

Mark any model as flagged.

### `ask_to_edit_resource`

Return whether the resource can be edited (i.e., no one is editing or the user asking to edit is currently editing it).
If it can be edited, then it also marks it as currently edited.

### `view_update_edit_resource`

A view method to inform that a resource is still being edited.

### `finish_edit_resource`

Marks that a resource is no longer being edited.
