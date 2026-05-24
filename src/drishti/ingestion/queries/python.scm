; Drishti Python Tree-sitter queries (US-03.02)
; Captures top-level and nested class/function definitions.

(class_definition
  name: (identifier) @symbol_name) @chunk_node

(function_definition
  name: (identifier) @symbol_name) @chunk_node
