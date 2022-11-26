import os
from time import sleep
from typing import Optional
from threading import Thread, Lock, main_thread, enumerate

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


class HabrResumeParserFromCsvToFiles:
    """
    Class to parse data by urls from csv file to files in folder resumes/,
    which will be created next to main.py file.
    """

    def __init__(self, csv_file_path: str):
        """
        :param csv_file_path: path to csv file. example: /root/tmp/test.csv
        """
        if not os.path.exists("resumes"):
            os.makedirs("resumes")

        self.__threading_lock = Lock()
        self.__list_of_unparsed_urls = []  # Saving urls with parsing error

        # Save urls to save in file in the end or when error had rose to avoid
        # re-parsing after errors
        self.__set_of_success_urls = set()
        if os.path.isfile(".success_urls"):
            with open(".success_urls", "rt") as file:
                self.__set_of_success_urls = set(file.readlines())

        try:
            self.__opened_csv_file = open(csv_file_path, "rt")
        except FileNotFoundError:
            print("Path to csv file is incorrect or file doesn't exist")
            raise

    def __exit__(self):
        with open(".success_urls", "at") as file:
            for url in self.__set_of_success_urls:
                file.write(url + "\n")

        self.__opened_csv_file.close()

    def get_links_with_errors_after_parsing(self):
        return self.__list_of_unparsed_urls

    def __get_next_url_from_csv_file(self) -> str:
        """
        Getting new line from opened csv file. During method work, variable
        self.__opened_csv_file will be locked as mutex.
        :return: url string
        """
        # It is made, because several threads could read the same url from file
        self.__threading_lock.acquire()
        next_url_string = next(self.__opened_csv_file, None)
        self.__threading_lock.release()

        if next_url_string:  # could be empty or None
            return "".join(next_url_string.strip().split("\""))

    def start_parsing(self) -> None:
        """
        Entrypoint. Start parsing from csv file.
        """
        url_to_parse = self.__get_next_url_from_csv_file()
        while url_to_parse is not None:
            if url_to_parse in self.__set_of_success_urls:
                continue

            print(f"started parsing {url_to_parse}\n")

            parsed_information = self.__parse_data_from_url(
                url=url_to_parse
            )

            # if rose parsing error
            if parsed_information is None:
                self.__list_of_unparsed_urls.append(url_to_parse)
                continue

            self.__save_page_html_into_file(parsed_information)
            print(f"Saved to file {parsed_information[1]}")
            self.__set_of_success_urls.add(url_to_parse)
            url_to_parse = self.__get_next_url_from_csv_file()

    def __save_page_html_into_file(
            self,
            information_to_save: tuple[str, str, str]
    ) -> None:
        """
        Saving file into file in format:
            first line:  page url
            second line: name and surname of human in resume
            third line:  page html
        File name is {username from url}.txt in resumes/ folder.
        """
        file_name = information_to_save[0].split("/")[-1]
        with open(f"resumes/{file_name}.txt", "wt") as file:
            information_in_format = "\n".join(information_to_save)
            file.writelines(information_in_format)

    def __parse_data_from_url(self, url: str) -> Optional[tuple[str, str, str]]:
        """
        Searching for values in html.
        :param url to get page from.
        :return: information about person in format or None if rose error
        (url to resume, name and surname, page html)
        """
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--start-maximized')

        driver = webdriver.Chrome(options=chrome_options)
        try:
            driver.get(url)
        except WebDriverException:
            print(f"Parsing error rose {url}")
            return None
        sleep(2)

        page_html = driver.page_source
        try:
            name_and_surname = driver.find_element(
                By.CSS_SELECTOR,
                'h1.page-title__title'
            ).text
        except NoSuchElementException:
            print(f"Link {url} rose error: human's name not found")
            return None

        driver.quit()

        return (url, name_and_surname, page_html)


if __name__ == "__main__":
    parser = HabrResumeParserFromCsvToFiles("habr.csv")

    # so many threads, because idle for a long time
    threads_amount = 20

    for _ in range(threads_amount):
        thread_to_add = Thread(target=parser.start_parsing)
        thread_to_add.start()

    urls_with_errors = parser.get_links_with_errors_after_parsing()
    if urls_with_errors:
        print("Pages with errors. Probably, they are incorrect")
        print(*urls_with_errors)

    main_thread = main_thread()
    for t in enumerate():
        if t is not main_thread:
            t.join()
