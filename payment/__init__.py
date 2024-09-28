class TransactionType:
    DEBIT = "Debit"
    CREDIT = "Credit"


transaction_type_choices = [
    (TransactionType.DEBIT, "Debit"),
    (TransactionType.CREDIT, "Credit"),
]

PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('cheque', 'Cheque'),
        ('stripe', 'Stripe')
    ]
