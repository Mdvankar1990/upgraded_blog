from date_format import DateFormatted


class Post:
    def __init__(self, title, subtitle, body, id, author, publishing_date: DateFormatted, blog_image):
        self.title = title
        self.subtitle = subtitle
        self.body = body
        self.id = id
        self.author = author
        self.publishing_date = publishing_date
        self.blog_image = blog_image
