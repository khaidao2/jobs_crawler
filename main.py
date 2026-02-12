from src.crawler.topcv.topcv_crawler import TopCVCrawler
from src.crawler.vietnam_works.vietnam_works import VNWorksCrawler
from src.crawler.careerviet.career_viet import CareerViet
def main():
    # vnworks_crawler = VNWorksCrawler(hits_per_page=50, sleep_time=0.8)
    # vnworks_crawler.run()

    # topcv_crawler = TopCVCrawler(db=None)
    # topcv_crawler.run()

    careerviet_crawler = CareerViet(max_page_safe=200)
    careerviet_crawler.run()
if __name__ == "__main__":
    main()