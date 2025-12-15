# Logging Query Language Specification

Use query syntax components with Advanced mode custom searches on the Logging Search page.

Markdown gathered from [here](https://docs.oracle.com/en-us/iaas/Content/Logging/Reference/query_language_specification.htm).

## User-facing response

In your response, include a link to the logging plugin with the search query, start time, end time, and region as URL query parameters. The URL will look like this

`https://cloud.oracle.com/logging/search?searchQuery=<search_query>&start=<time_start>&end=<time_end>&timeOption=custom`

The `searchQuery`, `start`, and `end` parameters all come from the inputs to the `search_log` MCP tool, but they must have URL encoding applied. The `start` and `end` time inputs must always be formatted wth RFC 3339 and must be supplied in UTC time zone. The `timeOption` query parameter must always be set to `custom`.

## Query Components

The logging query language processing is based on a data flow model. Each query can reference one or more logs, and produces a table dataset as a result. The query language provides several operators for searching, filtering, and aggregating structured and unstructured logs.

A logging query includes the following components:

- Log streams
- Fields
- Data types
- Stream expressions
- Pipe expressions
- Operators

## Log Streams

To begin your search, you must first define the set of logs you want to search. You can choose to search specific log objects, log groups, or compartments. You can mix and match as many logs as you need. The search scope is defined using the following pattern:

`search <log_stream> (,? <log_stream>)*`

The query language fetches log entries from the scope you provide, and constructs a log stream that you can filter, aggregate, and visualize.

Log stream:

`<log_stream> := "<compartment_ocid> ( /<log_goup_ocid> ( /<log_object_ocid> )? )?"`

Examples:

`search "compartmentOcid/logGroupNameOrOcid/logNameOrOcid"`

`search "compartmentOcid/logGroupNameOrOcid"`

`search "compartmentOcid"`

`search "compartmentOcid/logGroupNameOrOcid/logNameOrOcid", "compartmentOcid_2/logGroupNameOrOcid_2", "compartmentOcid_3"`

## Fields

All fields in log streams are case-sensitive. Although actual logs have indexed fields in lower case only, you can also create new fields in the query with mixed case:

```
search "..."
   | select event as EventName
```

Fields are in JSON notation, therefore, special characters must be in quotes.

`Fields: <field_name> := <identifier> (DOT <identifier>)*`

For Identifier:

`<identifier> := a-zA-Z_[a-zA-Z_0-9]* | ('"' (~'"' | '""')* '"')`

Examples:

- type
- data.message
- data.request.URL
- "type"
- "data"."message"
- "data.message" (not the same as "data"."message")
- data."$event"
- data."first name"
- data."an example of escaped ("") double quotes"

## Data Types

The following key data types are supported by the query language. These are (long and double) 8 bytes.

For details about the representation of the values of the corresponding types, see Literals.

- Strings
- Numbers (integer, float-point)
- Arrays
- Booleans
- Timestamps
- Intervals

## Stream Expressions

- Tabular operators
- Aggregate operators

## Pipe Expressions

A pipe (|) applies an operator on the left side to a stream expression on the right side. The pipe expression is a stream expression.

The operator on the right side of a pipe must consume only one stream (for example, aggregate operations, filters).

The left side becomes the "current stream" for the right side expression, making all fields in the current stream available according to short names. For example:
```
search "application"
  | where level = 'ERROR'
 
>>
{"timestamp": "2019-01-03T00:04:01", "level":"ERROR", "host":"host1", "message":"download failed...", "impact":2}
{"timestamp": "2019-01-03T00:06:39", "level":"ERROR", "host":"host2", "message":"reached 90% file size limit... ", "impact":4}
{"timestamp": "2019-01-03T00:06:59", "level":"ERROR", "host":"host2", "message":"reached 95% file size limit... ", "impact":5}
```

## Operators

The following are supported when performing advanced queries:

- Tabular operators
- Scalar operators
- Aggregate operators

## Tabular Operators

A tabular operator creates or modifies a log stream by filtering out or changing log entries. Also refer to BNF syntax notation. The following are tabular operators:

- search
- where
- top
- sort
- dedup
- select
- extend

### `search`

Constructs a log stream from actual log objects. Also see Log Streams for details, and Using the CLI for additional examples.

`search "compartmentOCID/loggroup1/logname1" "compartmentOCID/loggroup2/logname2" "compartmentOCID/loggroup3/logname3"`

### `where`

Filters the current log stream using a Boolean expression.

```
search "application"
  | where level = 'ERROR'
>>
{"timestamp": "2019-01-03T00:04:01", "level":"ERROR", "host":"host1", "message":"download failed...", "impact":2}
{"timestamp": "2019-01-03T00:06:39", "level":"ERROR", "host":"host2", "message":"reached 90% file size limit... ", "impact":4}
{"timestamp": "2019-01-03T00:06:59", "level":"ERROR", "host":"host2", "message":"reached 95% file size limit... ", "impact":5}
```

`where` is optional:

```
search "application"
   | level = 'ERROR'
```

Some example comparisons with numbers and Boolean field comparisons are the following:

`| data.statusCode = 200`

`| data.isPar`

If somebody passes in a resource to show the logs for, pass in the OCID with this format, SPECIFICALLY using `data.resourceId`

`| data.resourceId = 'ocid1.instance.oc1.iad...'`

You can perform a full text search by specifying a filter on the entire content of the log. A search on `logContent` returns any log line where a value matches your string. This functionality supports wildcards. For example:

```
search "application"
   | where logContent = 'ERROR' -- returns log lines with a value matching "ERROR"
```

```
search "application"
   | where logContent = '*ERROR*' -- returns log lines with a value containing "ERROR"
```

### `top`

Fetches only a specified number of rows from the current log stream, sorted based on some expression.

`<top> := top [0-9]+ by <expr>`

Examples:

- `top 3 by datetime`
- `top 3 by *`
- `top 3 by (a + b)`

A number of rows must be a constant positive integer, and a sorting expression must be provided.

```
search "application"
  | top 3 by impact
>>
{"timestamp": "2019-01-03T00:06:59", "level":"ERROR", "host":"host2", "message":"reached 95% file size limit... ", "impact":5}
{"timestamp": "2019-01-03T00:06:39", "level":"ERROR", "host":"host2", "message":"reached 90% file size limit... ", "impact":4}
{"timestamp": "2019-01-03T00:04:01", "level":"ERROR", "host":"host1", "message":"download failed...", "impact":2}
```

### `sort`

Sorts the current log stream by the specified columns, in either ascending (default) or descending order. The operator uses the "DESC" and "ASC" keywords to specify the type of the order. The default sort order is `asc`.

```
<sort> := sort by <sort_expr> (, <sort_expr>)*
<sort_expr> := <expr> (asc | desc)?
```

Example:

```
search "application"
  | sort by impact desc
>>
{"timestamp": "2019-01-03T00:06:59", "level":"ERROR", "host":"host2", "message":"reached 95% file size limit... ", "impact":5}
{"timestamp": "2019-01-03T00:06:39", "level":"ERROR", "host":"host2", "message":"reached 90% file size limit... ", "impact":4}
{"timestamp": "2019-01-03T00:04:01", "level":"ERROR", "host":"host1", "message":"download failed...", "impact":2}
{"timestamp": "2019-01-03T00:05:33", "level":"WARNING", "host":"host2", "message":"reached 70% file size limit... ", "impact":1}
{"timestamp": "2019-01-03T00:04:05", "level":"INFO", "host":" host1", "message":"host list updated..."}
{"timestamp": "2019-01-03T00:06:59", "level":"INFO", "host":" host2", "message":"fs clean up started..."}
```

More than one column can be used to specify the order:

```
search "application"
  | sort by host, impact desc
>>
{"timestamp": "2019-01-03T00:06:59", "level":"ERROR", "host":"host2", "message":"reached 95% file size limit... ", "impact":5}
{"timestamp": "2019-01-03T00:06:39", "level":"ERROR", "host":"host2", "message":"reached 90% file size limit... ", "impact":4}
{"timestamp": "2019-01-03T00:05:33", "level":"WARNING", "host":"host2", "message":"reached 70% file size limit... ", "impact":1}
{"timestamp": "2019-01-03T00:06:59", "level":"INFO", "host":" host2", "message":"fs clean up started..."}
{"timestamp": "2019-01-03T00:04:01", "level":"ERROR", "host":"host1", "message":"download failed...", "impact":2}
{"timestamp": "2019-01-03T00:04:05", "level":"INFO", "host":" host1", "message":"host list updated..."}
```

### `dedup`

Processes the current log stream by filtering out all duplicates by specified columns. If more than one column is specified, all columns have to be delimited by commas.

`<dedup> := dedup <expr> (, <expr>)`

Examples

```
search "application"
  | dedup host
>>
{"timestamp": "2019-01-03T00:04:01", "level":"ERROR", "host":"host1", "message":"download failed...", "impact":2}
{"timestamp": "2019-01-03T00:05:33", "level":"WARNING", "host":"host2", "message":"reached 70% file size limit... ", "impact":1}
```

```
search "application"
  | dedup host, impact
{"timestamp": "2019-01-03T00:04:01", "level":"ERROR", "host":"host1", "message":"download failed...", "impact":2}
{"timestamp": "2019-01-03T00:05:33", "level":"WARNING", "host":"host2", "message":"reached 70% file size limit... ", "impact":1}
{"timestamp": "2019-01-03T00:06:39", "level":"ERROR", "host":"host2", "message":"reached 90% file size limit... ", "impact":4}
{"timestamp": "2019-01-03T00:06:59", "level":"ERROR", "host":"host2", "message":"reached 95% file size limit... ", "impact":5}
```

### `select`

Applies a series of named scalar expressions to the current log stream. See summarize for an aggregation version of select.

```
<select> := select <select_expr> (, <select_expr>)*
<select_expr> := ( * | <expr> (as <identifier>)? )
```

Example:

```
search "application"
  | select level, host, impact+10 as impact, timestamp
>>
{"level":"ERROR", "host":"host1", "impact": 12, "timestamp": "2019-01-03T00:04:01"}
{"level":"INFO", "host":" host1", "timestamp": "2019-01-03T00:04:05"}
{"level":"WARNING", "host":"host2", "impact": 11, "timestamp": "2019-01-03T00:05:33"}
{"level":"ERROR", "host":"host2", "impact": 14, "timestamp": "2019-01-03T00:06:39"}
{"level":"ERROR", "host":"host2", "impact": 15, "timestamp": "2019-01-03T00:06:59"}
{"level":"INFO", "host":" host2", "timestamp": "2019-01-03T00:06:59"}
```

You MUST only use this if you are certain in the property values to select. Do not guess the property names.

### `extend`

Extends the current log stream with a computed column.

`<extend> := extend <expr> (as <identifier>)?`

Example:

```
search "application"
  | extend concat(host, 'us.oracle.com') as fqn
>>
{"timestamp": "2019-01-03T00:04:01", "level":"ERROR", "host":"host1", "message":"download failed...", "impact":2, "fqn": "host1.us.oracle.com"}
{"timestamp": "2019-01-03T00:04:05", "level":"INFO", "host":" host1", "message":"host list updated...", "fqn": "host1.us.oracle.com"}
{"timestamp": "2019-01-03T00:05:33", "level":"WARNING", "host":"host2", "message":"reached 70% file size limit... ", "impact":1, "fqn": "host2.us.oracle.com"}
{"timestamp": "2019-01-03T00:06:39", "level":"ERROR", "host":"host2", "message":"reached 90% file size limit... ", "impact":4, "fqn": "host2.us.oracle.com"}
{"timestamp": "2019-01-03T00:06:59", "level":"ERROR", "host":"host2", "message":"reached 95% file size limit... ", "impact":5, "fqn": "host2.us.oracle.com"}
{"timestamp": "2019-01-03T00:06:59", "level":"INFO", "host":" host2", "message":"fs clean up started...", "fqn": "host2.us.oracle.com"}
```

## Scalar Operators

Scalar operators are applicable to individual values.

Arithmetic operations are the following:

- `+`
- `-`
- `*`
- `/`
  
Boolean operators are the following:

- `and`
- `or`

Unary operator:

- `-(<expr>)`

Comparison operators are the following (numeric expressions only):

- `<expr> > <expr>`
- `<expr> >= <expr>`
- `<expr> <= <expr>`
- `<expr> < <expr>`
- `<expr> = <expr>`
- `<expr> != <expr>`

String comparison:

- `<expr> = <expr>`

Functions:

- `not (<expr>)`
- `contains_ci/contains_cs (<expr>, <expr>, (true | false))`

    The last parameter is case-sensitive.

- `rounddown (<expr>, '[0-9]+(d | h | m | s)')`

    The last parameter is the time interval in days, hours, minutes, or seconds.

- `time_format(datetime, <format>)`

    Format a time to a string

- `concat (<axpr>, <expr>)`
- `upper (<expr>)`
- `lower (<expr>)`
- `substr (<expr>, [0-9]+ (, [0-9]+)?)`
    
    The second argument is the start index, while the third argument is optional, namely, how many characters to take.

- `isnull (<expr>)`
- `isnotnull (<expr>)`

## Aggregate Operators

### `count`

Calculates a number of rows in the current log stream:

```
search "application"
  | count
>>
{"count": 6}
```

### `summarize`

Groups the current log stream by the specified columns and time interval, and aggregates using named expressions. If grouping columns are not specified, `summarize` aggregates over the whole stream.

```
search "application"
  | summarize count(impact) as impact by level, rounddown(datetime,  '1m') as timestamp
```

You MUST ONLY use this if you are certain in the property values to summarize. Do NOT guess the property names. Do NOT attempt to group by `data.principal.identity` or `data.principal.user`. 

## Special Columns

### `logContent`

`logContent` is a special column which represents the text of the whole original message. For example:

```
search "application"
   | where logContent = '*ERROR*' -- returns log lines with a value containing "ERROR"
```

## Comments

Both single line and multi-line comments are supported, for example:

```
search "application"
  | count -- this is a single line comment
```

```
/* this is a
   multi-line
   comment
*/
```

## Identifiers

Identifiers are the names of all available entities in the query. An identifier can reference a field in the current log stream, or a parameter defined in the beginning of the query. Identifiers have the following format:

`name: \$?[a-zA-Z_][a-zA-Z_0-9]*`

For example: `level`, `app_severity`, `$level`.

The quoted form allows special symbols in the names (except double quotes):

`name: "[^"]+"`

For example: `"opc-request-id"`, `"-level"`.

All parameter references start with a dollar sign (`$`), for example: `$level`.

## Literals

| Type              | Examples            |
|-------------------|---------------------|
| string            | 'hello', 'world\'!' |
| wildcard pattern  | "acc-*"             |
| integer           | -1, 0, +200         |
| float             | 1.2, 0.0001, 1.2e10 |
| array             | [1,2,3,4], []       |
| interval          | 3h, 2m              |
| nullable          | null                |

## Functions

Scalar functions are the following:

- isnull(expr1)
- concat(expr1, ...)

Aggregate functions are the following:

- sum(expr1)
- avg(expr1)
- min(expr1)
- max(expr1)
- count(): Counts a number of rows.
- count(expr): Counts a number of non-null expr values.
- first(expr1)
- last(expr1)

## System parameters

All parameters with the `prefex` "query." are reserved. The following parameters are supported:

| Name          | Type                                      | Example                  | Description                                  |
|---------------|-------------------------------------------|--------------------------|----------------------------------------------|
| `query.from ` | String with date time in ISO 8601 format. | '2007-04-05T14:30'       | Specifies starting time of the query window. |
| `query.to`    | String with date time in ISO 8601.        | '2007-04-05T14:30+05:00' | Specifies end time of the query window.      |
