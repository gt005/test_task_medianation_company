"""
В этой задаче лучше использовать многопоточность, а не многопроцессорность,
так как процессы очень тяжеловесные и будут почти все время простаивать в
ожидании http ответа. А потоки реализованы внутри одного процесса и будут
поочереди засыпать, дожидаясь ответа, что позволит снизить время простоя.
"""
import os
import time
from time import sleep
from threading import Thread, Lock, main_thread, enumerate

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class HabrResumeParserFromCsvToFiles:
    """
    Class to parce data by urls from csv file to files in folder resumes/,
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

        try:
            self.__opened_csv_file = open(csv_file_path, "rt")
        except FileNotFoundError:
            print("Path to csv file is incorrect or file doesn't exist")
            raise

    def __exit__(self):
        self.__opened_csv_file.close()

    def __get_next_url_from_csv_file(self) -> str:
        """
        Getting new line from opened csv file. During method work,
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
        Start parsing from csv file.
        """
        url_to_parse = self.__get_next_url_from_csv_file()
        while url_to_parse is not None:
            print(url_to_parse, '\n')
            parsed_information = self.__parse_data_from_url(
                url=url_to_parse
            )
            self.__save_page_html_into_file(parsed_information)
            print(f"saved to file{parsed_information[1]}\n")
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
        File name is {url}.txt in resumes/ folder.
        """
        file_name = information_to_save[0].split("/")[-1]
        with open(f"resumes/{file_name}.txt", "wt") as file:
            information_in_format = "\n".join(information_to_save)
            file.writelines(information_in_format)

    def __parse_data_from_url(self, url: str) -> tuple[str, str, str]:
        """
        Searching for values in html.
        :param url to get page from.
        :return: information about person in format
        (url to resume, name and surname, page html)
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        sleep(2)

        page_html = driver.page_source
        name_and_surname = driver.find_element(
            By.CSS_SELECTOR,
            'h1.page-title__title'
        ).text

        driver.quit()

        return (url, name_and_surname, page_html)


if __name__ == "__main__":
    start = time.monotonic()
    parser = HabrResumeParserFromCsvToFiles("habr1.csv")
    threads_amount = 1

    for _ in range(threads_amount):
        thread_to_add = Thread(target=parser.start_parsing)
        thread_to_add.start()

    main_thread = main_thread()
    for t in enumerate():
        if t is not main_thread:
            t.join()

    print((time.monotonic() - start) / 30)

