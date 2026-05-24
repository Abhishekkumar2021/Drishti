; Drishti Java Tree-sitter queries (US-03.03)

(package_declaration
  (scoped_identifier) @symbol_name) @chunk_node

(interface_declaration
  name: (identifier) @symbol_name) @chunk_node

(class_declaration
  name: (identifier) @symbol_name) @chunk_node

(method_declaration
  name: (identifier) @symbol_name) @chunk_node

(constructor_declaration
  name: (identifier) @symbol_name) @chunk_node

(field_declaration
  declarator: (variable_declarator
    name: (identifier) @symbol_name)) @chunk_node
