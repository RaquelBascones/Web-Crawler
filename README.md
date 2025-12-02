# Mini Web Crawler - Link Extraction, Summarization and Classification

## Table of Contents

1. [About the Project](#1-about-the-project)
2. [Key Features](#2-key-features)
3. [Project Structure](#3-project-structure)
4. [Technologies Used](#4-technologies-used)
5. [Execution](#5-execution)


---

## 1. About the Project

This project is a mini web crawler developed in **Python** that allows the user to analyze a web page, extract all its links, automatically generate summaries of each linked page, store all the information in a **SQLite** database and display the results in a dynamically generated **HTML** file.

The project also includes a basic **Artificial Intelligence text classification system** that assigns a category to the analyzed web page. The main objective is to combine web scraping, database management, text processing and machine learning in a single functional application.

---

## 2. Key Features

* **Web Scraping:** Automatic download of web pages using the `requests` library.
* **Link Extraction:** Extraction of hyperlinks using regular expressions.
* **Text Extraction:** Real content extraction using `trafilatura`.
* **Automatic Summarization:** Generation of short summaries for each extracted link.
* **Automatic Translation:** Summaries are translated into Spanish using `googletrans`.
* **Database Storage:** All data is stored in a SQLite database.
* **HTML Visualization:** Automatic generation of an HTML file to display results.
* **Machine Learning Classification:** Page classification using TF-IDF and Naive Bayes.

---

## 3. Project Structure


* **SuperNenasPEC3.py:** Main script that runs the crawler.
* **crawler.db:** SQLite database where all links and summaries are stored.
* **supernenas.html:** Automatically generated HTML file showing the results.
* **README.md:** Project documentation.

---

## 4. Technologies Used

* **Programming Language:** Python 3.9+
* **Database:** SQLite
* **Web Scraping:** requests, trafilatura
* **Text Processing:** googletrans
* **Machine Learning:** scikit-learn
* **Visualization:** HTML and CSS (auto-generated)

---

## 5. Execution
  python SuperNenasPEC3.py

  If you want to test another website, you must first clear the terminal and then repeat the same execution process again:

**Clear the terminal:**

```bash
clear


```
After execution:

- The `crawler.db` database is created or updated.
- The `supernenas.html` file is generated with all extracted links and their summaries.
- The main web page is automatically classified into one of the following categories:
  - noticias
  - deportes
  - tienda
  - tecnologia

To view the results, simply open the `supernenas.html` file in any web browser.

