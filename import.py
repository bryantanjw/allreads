import csv
import os

from flask import Flask, render_template, request
from models import *

def main():
    f = open("books.csv")
    reader = csv.reader(f)

    # Skip header
    next(reader, None)

    for isbn, title, author, year in reader:
        book = Book(isbn=isbn, title=title, author=author, year=year)
        db.session.add(book)
        print(f"Added {isbn} {title} by {author} in year {year}.")
    db.session.commit()
