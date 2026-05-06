PRODUCT_PROMPTS = [
    "Build a CRM with login, contacts, companies, deals, dashboard, role-based access, premium plan with payments, and admin analytics.",
    "Create an ecommerce admin app with products, orders, customers, payments, dashboard, and admin reports.",
    "Build a helpdesk for support tickets with agents, customers, ticket priority, search, and analytics.",
    "Make an invoicing app with clients, invoices, payment status, dashboard, and email notifications.",
    "Create a project management app with projects, tasks, owners, due dates, dashboard, and role permissions.",
    "Build a lightweight HR app with employees, onboarding tasks, admin dashboard, and login.",
    "Create a course platform with users, premium subscriptions, products, orders, and analytics.",
    "Build a sales pipeline tracker with leads, contacts, deals, admin analytics, and CSV-style dashboards.",
    "Make a customer portal with login, tickets, invoices, billing, and customer-only access.",
    "Create an operations tracker with projects, tasks, dashboard metrics, admin access, and notifications.",
]

EDGE_CASE_PROMPTS = [
    "Build an app.",
    "CRM but no database, yet users must save contacts and deals.",
    "Make a dashboard with payments and analytics but no login for anyone.",
    "Only admins can use it, but customers should manage their own orders.",
    "Build something for tickets maybe with reports idk.",
    "Create a premium-only product app, but free users must access every premium feature.",
    "Make a support app with ticket fields that include email, priority, status, and invisible internal notes.",
    "Need login and roles for contacts, contacts, contacts and duplicate leads.",
    "Build a finance tool with invoices and payments, but do not store invoice data.",
    "Make a CRM that admins cannot access, admins can see analytics, and users can edit contacts.",
]

ALL_PROMPTS = PRODUCT_PROMPTS + EDGE_CASE_PROMPTS
