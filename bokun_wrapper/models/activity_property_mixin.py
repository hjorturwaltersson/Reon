class ActivityPropertyMixin:
    @property
    def price_categories(self):
        return self.json['pricingCategories']

    @property
    def default_price_category(self):
        return next(filter(lambda c: c['defaultCategory'], self.price_categories), None)

    @property
    def default_price_category_id(self):
        return self.default_price_category['id']

    @property
    def child_price_category(self):
        try:
            return next(filter(
                lambda c: 'CHILD' in (c['ticketCategory'] + c['title']).upper(),
                self.price_categories
            ))
        except StopIteration:
            return self.default_price_category

    @property
    def child_price_category_id(self):
        return self.child_price_category['id']

    @property
    def teenager_price_category(self):
        try:
            return next(filter(
                lambda c: 'TEEN' in (c['ticketCategory'] + c['title']).upper(),
                self.price_categories
            ))
        except StopIteration:
            return self.child_price_category

    @property
    def teenager_price_category_id(self):
        return self.teenager_price_category['id']
