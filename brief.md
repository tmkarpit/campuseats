# CampusEats Brief

## What the system does

CampusEats is a campus food ordering system. It lets students browse food options from campus dining locations or approved local vendors, place orders, pay for meals, and choose pickup or delivery. It also gives vendors a way to publish menus, receive orders, update order status, and manage availability during busy campus hours.

The main purpose is to make campus food ordering faster and more predictable. Students should be able to see what is available before walking across campus, and vendors should be able to handle orders without relying only on in-person lines.

## Who uses it

Students use CampusEats to find meals, customize items, place orders, track status, and pick up or receive food. Vendors and dining staff use it to maintain menus, accept or reject orders, prepare food, and mark orders as ready. Delivery workers or campus runners use it to claim delivery tasks and update delivery progress. Administrators use it to manage users, vendors, service areas, fees, and reports.

## Nouns

- Student
- Vendor
- Dining location
- Menu
- Menu item
- Category
- Cart
- Order
- Order item
- Payment
- Receipt
- Pickup location
- Delivery address
- Delivery task
- Driver or runner
- Promotion
- Review
- Notification
- Administrator

## Verbs

- Register
- Log in
- Browse menus
- Search food
- Filter vendors
- View item details
- Add item to cart
- Customize item
- Place order
- Pay for order
- Cancel order
- Accept order
- Reject order
- Prepare order
- Mark order ready
- Assign delivery
- Pick up order
- Deliver order
- Track status
- Send notification
- Update menu
- Set availability
- Review vendor
- Generate report

## Early service boundaries

CampusEats can be divided into services around accounts, menus, orders, payments, delivery, notifications, and administration. The order service is the center of the system because it connects the student, vendor, payment, and pickup or delivery workflow. The menu service defines what can be ordered, while the notification service keeps each user informed as the order moves from placed to ready or delivered.
