; Drishti JavaScript Tree-sitter queries (US-03.04)

(class_declaration
  name: (identifier) @symbol_name) @chunk_node

(function_declaration
  name: (identifier) @symbol_name) @chunk_node

(method_definition
  name: (property_identifier) @symbol_name) @chunk_node

(generator_function_declaration
  name: (identifier) @symbol_name) @chunk_node

(lexical_declaration
  (variable_declarator
    name: (identifier) @symbol_name
    value: [(arrow_function) (function_expression)])) @chunk_node
