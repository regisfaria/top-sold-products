# Here i'll be writting some utilitys that will help on the main codes

# I must call this class as Product(price='x.xx', name='product', ...)
class Product(object):
    # update this when needed
    def __init__(self, **kargs):
        self.properties = {}
        for key, value in kwargs.items():
            properties[key] = value


def write_to_csv(product_list):
    # Here i'll write the products into a csv
    pass