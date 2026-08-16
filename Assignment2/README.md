# CampusEats — Assignment 2

## Included
- design.pdf — capabilities, service ownership, contracts, full placeOrder specification, validation
- services.drawio — editable service design diagram
- services.png / services.pdf — exported service diagram
- schema.drawio — editable ER/service-boundary diagram
- schema.png / schema.pdf — exported schema diagram
- schema.sql — PostgreSQL CREATE TABLE sketch

## Service benchmark
1. Identity Service
2. Catalogue Service
3. Order Service
4. Payment Service
5. Notification Service

The main operation is `Order Service.placeOrder`.

## Important design rule
No database table is shared between services. Cross-service IDs such as `student_id`, `item_id`, and `order_id` are opaque references and are intentionally not declared as foreign keys across service boundaries.
