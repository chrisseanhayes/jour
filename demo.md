# YouTube demo script: Meet `jour`

## Opening

**[ON SCREEN: Terminal, in the `jour` repository]**

**HOST:**  
Ever jot down a thought, a reminder, or a task in the terminal and then
immediately forget where you put it? In this video, I’ll show you `jour`: a
small command-line journal that lets you capture notes, organize them with
tags, and query them later.

We’ll start with the basics, then turn it into a lightweight code-todo tracker
using a reusable query.

**[OPTIONAL: Start an isolated demo shell]**

```sh
./demo.sh
```

**HOST:**  
I’m using the demo shell here, so the examples won’t mix with my regular
journal. The demo container opens with `nano` as its editor.

## What is `jour`?

**[ON SCREEN: Show the `jour` command and a short list]**

**HOST:**  
`jour` is a command-line journal. A note has a body, a unique hash, and
optionally some tags. You can make notes right in the terminal or write them in
your editor. Later, you can list, search, edit, archive, or delete them.

Let’s make our first note.

## Make a note

**[ON SCREEN: Type the command]**

```sh
jour make --note "First day using jour: keeping the useful bits close."
```

**HOST:**  
The `--note` option gives `jour` the note text directly. If I leave that
option off in an interactive terminal, `jour make` opens my configured editor
instead.

## Add a tag

**[ON SCREEN: Create a note with explicit tags]**

```sh
jour make --note "Plan the next jour release." --tag work,planning
```

**HOST:**  
Tags give us a quick way to group notes. I can pass several at once as a
comma-separated list with `--tag`, or use the shorter `-t`.

There’s also a handy shortcut: hashtags in the note body become tags
automatically.

**[ON SCREEN: Create a note with hashtags]**

```sh
jour make --note "Try a new workflow for #jour and #ideas."
```

**HOST:**  
That adds the tags `jour` and `ideas`—without the hash symbol. I can see the
tags I’ve used with `jour tags list`, or see notes for a particular tag with
`jour tags show jour`.

## List notes

**[ON SCREEN: List the notes]**

```sh
jour list
```

**HOST:**  
Here are my active notes in chronological order. Each line shows the note’s
hash, tags, and a short preview. I’ll use a hash from this list whenever I
want to work with a specific note.

## Edit a note

**[ON SCREEN: Replace the example text with a hash from the list]**

```sh
jour edit HASH_FROM_LIST
```

**HOST:**  
`jour edit` opens the note in my editor. I can revise the text, or add a
hashtag like `#done`. Save and close the editor, and `jour` refreshes the
note’s tags.

## Archive a note

**[ON SCREEN: Archive a note using its hash]**

```sh
jour archive HASH_FROM_LIST
```

**HOST:**  
Archiving hides a note from the regular list, but keeps it in the journal.
To see archived notes, add `--show-archived` to `jour list`.

And if I change my mind, I can restore the note with `--undo`.

**[ON SCREEN: Restore the note]**

```sh
jour archive --undo HASH_FROM_LIST
```

## Delete a note

**[ON SCREEN: Show the command, but do not run it on a note you need]**

```sh
jour delete HASH_FROM_LIST
```

**HOST:**  
Unlike archiving, deleting permanently removes the note. So double-check that
hash before running this one.

## List with a query

**[ON SCREEN: Query for notes tagged `jour`]**

```sh
jour list --query "[?contains(tags, 'jour')].{id: id, body: body}"
```

**HOST:**  
Now for the more flexible part. `jour list --query` accepts a JMESPath
expression. Instead of the usual preview, it returns JSON, so I can filter
notes and choose exactly which fields I want back.

Here I’m selecting notes tagged `jour`, and returning just each note’s hash
and body. Let’s use that to build something practical.

## Flexible workflow: track code todos

**[ON SCREEN: Create two code-todo notes]**

```sh
jour make --note "Fix the archive undo edge case." --tag code,todo,jour
jour make --note "Add a test for query output." --tag code,todo,jour
```

**HOST:**  
I’m using three tags consistently: `code` says what kind of task it is,
`todo` says it still needs work, and `jour` is the project name.

Now I’ll define a query for open code todos in this project. A task is open as
long as it doesn’t have the `done` tag.

**[ON SCREEN: Define the reusable query]**

```sh
TODO_QUERY="[?contains(tags, 'code') && contains(tags, 'todo') && contains(tags, 'jour') && !contains(tags, 'done')].{id: id, tags: tags, body: body}"
```

**HOST:**  
The nice thing about saving this expression in a shell variable is that I
don’t have to retype it. I can run the query whenever I want to see the open
tasks.

**[ON SCREEN: Run the query]**

```sh
jour list --query "$TODO_QUERY"
```

### Make the output easier to scan

**HOST:**  
Because the query returns JSON, I can pass it through other command-line
tools. Here I’ll use JavaScript to turn each result into a tab-separated row,
then use `awk` to line up the hash and task.

This example uses Node.js. If your `js` command runs Node-compatible JavaScript,
you can set `JS=js`; otherwise the default below is `node`.

**[ON SCREEN: Format results with JavaScript and `awk`]**

```sh
JS=${JS:-node}

jour list --query "$TODO_QUERY" |
  "$JS" -e '
    let input = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", chunk => input += chunk);
    process.stdin.on("end", () => {
      for (const note of JSON.parse(input)) {
        console.log(`${note.id}\t${note.body.replace(/\s+/g, " ")}`);
      }
    });
  ' |
  awk -F "\t" '{ printf "%-24s %s\n", $1, $2 }'
```

**HOST:**  
One small portability note: `js` means different things on different
systems. Make sure it runs Node-compatible JavaScript, or just leave `JS` set
to `node`. And if I only need to filter the notes, I don’t need JavaScript or
`awk` at all—the JMESPath query works on its own.

### Mark a todo done

**[ON SCREEN: Open one task using its hash from the results]**

```sh
jour edit HASH_FROM_LIST
```

**HOST:**  
To finish a task, I’ll add `#done` to its note and save. Since hashtags become
tags, that note stops matching the open-todo query. No separate task database
or status command needed.

I can make another reusable query to see completed tasks instead.

**[ON SCREEN: Define and run the completed-todo query]**

```sh
DONE_QUERY="[?contains(tags, 'code') && contains(tags, 'todo') && contains(tags, 'jour') && contains(tags, 'done')].{id: id, body: body}"
jour list --query "$DONE_QUERY"
```

**HOST:**  
I could keep `TODO_QUERY` and `DONE_QUERY` in my shell profile, or save them in
a small project script. And if I also want a completed note out of my normal
journal list, I can archive it—the `done` tag and archiving are separate.

## Wrap-up

**[ON SCREEN: Show `jour list`, then the todo query]**

**HOST:**  
That’s the basic idea: use `jour` to capture notes, tags to organize them, and
queries to build the workflow you want. Start with a couple of tags, keep the
query somewhere reusable, and you’ve got a simple project todo list right in
your journal.

Thanks for watching. What would you use tags and queries for? Let me know, and
I’ll see you in the next one.
