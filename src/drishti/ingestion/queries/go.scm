; Drishti Go Tree-sitter queries (US-03.05)

(package_clause
  (package_identifier) @symbol_name) @chunk_node

(type_declaration
  (type_spec
    name: (type_identifier) @symbol_name)) @chunk_node

(function_declaration
  name: (identifier) @symbol_name) @chunk_node

(method_declaration
  name: (field_identifier) @symbol_name) @chunk_node
