# ToolFavor public number policy (draft)

- Account `users.id` is the immutable internal database key.
- Public display number is a distinct unique identifier, tracked in `public_numbers`.
- Founder number **#1** is reserved for COLDDCC. It must only be assigned after authenticated founder ownership is verified, never based on a client-supplied username.
- Standard numbers are free, automatically generated, and assigned atomically. Numbers may look random but must be collision-checked. No promise of sequential registration order.
- Premium numbers are reserved and require a verified payment plus a transactional assignment flow; pricing is provisional.
- A public number is not reassigned to another user once assigned, even if an account is closed. Use `retired` status to protect history.
- A user may own only one active display number. On premium upgrades, the previous number is retired, not recycled.
- Public number reservation is not proof of purchase or ownership. No checkout or payment integration is active.
- Do not expose email, payment status, or private user information in public creator APIs.
- The creator profile UI and public routing will be updated when registration and deployment are configured.
