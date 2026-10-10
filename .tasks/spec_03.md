# Specification: `jour notes edit {hash}`

## Description
A command to open a specific journal entry for editing in the system's default editor.

## Command Syntax
`jour notes edit <hash>`

## Functional Requirements
1. **Hash Resolution**: The system must look up the file path associated with the provided `<hash>` in the local database.
2. **Editor Selection**: The system must identify the editor to use. It should check the configuration for a preferred editor, falling back to a system default (e.g., `vi` or `nano`) if none is specified.
3. **File Opening**: The system must launch the editor and open the file located at the resolved path.
4. **Process Blocking**: The CLI should wait for the editor process to exit before returning control to the shell.

## Error Handling
- **Invalid Hash**: If the provided hash does not exist in the database, return an error: `Error: Note with hash <hash> not found.`
- **Missing File**: If the database entry exists but the file is missing from the filesystem, return an error: `Error: File for hash <hash> could not be found on disk.`
- **Editor Failure**: If the editor fails to launch, return an error message.

## Technical Notes
- Requires integration with `jour_cli/db.py` to fetch file paths by hash.
- Requires integration with `jour_cli/config.py` to retrieve editor settings.
- Implementation will likely reside in `jour_cli/notes.py`.
