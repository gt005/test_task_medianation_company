current_dir := $(shell pwd)

all: test_tast_medianation_container
	docker run -it --rm -v $(current_dir)/resume:/src/resumes --name test_tast_medianation_container test_tast_medianation_image

test_tast_medianation_container:
	docker build -t test_tast_medianation_image .

chrome_driver_to_test:
	docker run -d -p 4444:4444 selenium/standalone-chrome

stop:
	docker stop test_tast_medianation_container
	docker rmi test_tast_medianation_image
