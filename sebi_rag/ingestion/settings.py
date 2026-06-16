BOT_NAME = "sebi_rbi_crawler"
SPIDER_MODULES = ["ingestion.spiders"]
DOWNLOAD_DELAY = 1.0
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 1
ROBOTSTXT_OBEY = True
ITEM_PIPELINES = {
    "ingestion.pipelines.DeduplicatePipeline": 300,
    "ingestion.pipelines.SaveMetaPipeline": 400,
}
LOG_LEVEL = "INFO"
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
