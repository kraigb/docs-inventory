# Script to use the Cognitive Services key phrase extraction API to process the contents
# of source files listed in a CSV file. The input file should be relatively small to minimize
# service usage (and not exceed free tier limits).
#
# Yo provide the endpoint and API key for your specific subscription through command line args.

import sys

allowlist = ["ACR", "AKS", "AKS cluster", "ARCore", "ARM", "Anomaly Detector API's", "Anomaly Detector REST API", "Apache Cassandra", "Apache Hadoop HDFS", "Apache Hive", "Apache Kafka", "Apache Maven", "Apache Spark", "Apache Storm", "Apache TinkerPop", "App Service", "App Service Authentication", "Application Insights Java SDK", "Application Insights SDK", "Application Screenshot", "Async Java", "Async Java SDK", "Azure AD", "Azure AD B2C", "Azure AD User Provisioning Service", "Azure Active Directory", "Azure Active Directory B2C", "Azure Active Directory accounts", "Azure Active Directory integration", "Azure App Configuration", "Azure App Service", "Azure App Service Web Apps", "Azure Application Insights", "Azure Batch", "Azure Blob Storage", "Azure Blob storage", "Azure CLI", "Azure Cache", "Azure Cloud Service", "Azure Cloud Shell", "Azure Cognitive Service", "Azure Cognitive Services", "Azure Cognitive Services Computer Vision SDK", "Azure Cognitive Services account", "Azure Command Line Interface", "Azure Container Instances", "Azure Container Register", "Azure Container Service", "Azure Cosmos DB", "Azure Data Explorer", "Azure Data Factory", "Azure Data Lake Analytics", "Azure Data Lake Storage", "Azure Database", "Azure Databricks", "Azure Dev Spaces", "Azure DevOps Projects", "Azure DevOps Services", "Azure Digital Twins", "Azure Event Grid", "Azure Event Hubs", "Azure Face API", "Azure Face REST API", "Azure Form Recognizer REST API", "Azure Functions", "Azure HDInsight", "Azure HDInsight Hadoop", "Azure IoT Device Provisioning Service", "Azure IoT Edge", "Azure IoT Hub", "Azure IoT Hub Device Provisioning Service", "Azure IoT Java device SDK", "Azure Kubernetes Service", "Azure Machine Learning", "Azure Machine Learning SDK", "Azure Machine Learning Studio", "Azure Map Control API", "Azure Maps", "Azure Monitor Application Insights", "Azure Notebook", "Azure Notebooks", "Azure Notification Hubs", "Azure Pipelines", "Azure PowerShell", "Azure Repos", "Azure Resource Manager template", "Azure SQL Data Warehouse", "Azure SQL Database", "Azure SQL Database Machine Learning Services", "Azure SQL database", "Azure Service Fabric", "Azure SignalR Service", "Azure Spatial Anchors", "Azure Storage", "Azure Storage Blobs", "Azure Storage Client Library", "Azure Storage client library", "Azure Stream Analytics", "Azure Time Series Insights", "Azure Toolkit", "Azure Traffic Manager", "Azure VM", "Azure Web App", "Azure appservice", "Batch", "Batch service", "Bing Answer Search API", "Bing Custom Search API", "Bing Custom Search SDK", "Bing Custom Search endpoint", "Bing Custom Search instance", "Bing Entity Search API", "Bing Entity Search REST API", "Bing Entity Search SDK", "Bing Image Search API", "Bing Image Search REST API", "Bing Image Search SDK", "Bing Local Business Search API", "Bing Maps API", "Bing Maps service", "Bing News Search API", "Bing News Search REST API", "Bing News Search SDK", "Bing Search APIs", "Bing Spell Check REST API", "Bing Video Search API", "Bing Video Search REST API", "Bing Video Search SDK", "Bing Video Search features", "Bing Visual Search API", "Bing Visual Search REST API", "Bing Visual Search SDK", "Bing Visual Search service", "Bing Web Search", "Bing Web Search API", "Bing Web Search REST API", "Bing Web Search SDK", "Bing client", "Bing client ID", "Bing search API", "Bing-Web", "CD", "CI", "CLI", "CLI utility", "Cassandra", "Cisco Spark", "Cloud Shell", "Cognitive Services Computer Vision documentation", "Cognitive Services Face Android", "Cognitive Services Pricing - Bing Search API", "Cognitive Services Speech SDK", "Computer Vision", "Computer Vision API Python", "Computer Vision REST API", "Computer Vision algorithms", "Computer Vision service", "Computer Vision's REST API", "Continuous Delivery", "Continuous Integration", "Continuous integration", "Cosmos DB", "Cosmos account", "Cosmos database", "Custom Decision Service", "Custom Vision Java SDK", "Custom Vision Python SDK", "Custom Vision SDK", "Custom Vision Service", "Custom Vision web server", "Data Explorer", "Data Factory pipeline", "Data Lake Store", "Databricks", "Durable Functions", "ETL", "FCM", "FastCGI", "HDInsight", "HOLTop", "HPC", "HSM", "Hardware Security Module", "IIS", "Ink Recognizer API", "Ink Recognizer REST API", "IntellSense", "IoT Device Provisioning Service", "IoT EdgeIoT Hub", "IoT Hub Device Provisioning Service", "IoT Hub device streams", "IronPython", "JDBC driver", "JRE", "JSP", "Jade", "Java Service Fabric Reliable Services", "Java Service SDK", "JavaScript SPA", "Jedis", "Jinja", "Jupyter", "Jupyter Notebook", "Jupyter Notebook Server", "Jupyter notebook", "Jupyter notebooks", "JupyterLab", "Kafka Consumer API", "Kafka Producer API", "Kafka-enabled", "Kafka-enabled", "KeyPhraseExtraction", "LUIS", "LUIS", "Livy", "MEAN stack", "MLlib", "MNIST data", "Machine Learning Studio", "Maps APIs", "Maps search service", "Microsoft Azure", "Microsoft Azure Cosmos DB", "Microsoft Azure IoT Central application", "Microsoft Azure IoT Hub", "Microsoft Azure Machine Learning Studio", "Microsoft Azure storage account", "Microsoft Cognitive Services", "Microsoft Genomics", "Microsoft Graph API", "Microsoft Power BI", "Microsoft QnA Maker API", "MyBinder", "Notification Hub REST APIs", "Notification Hub REST interface", "Notification Hubs REST APIs", "Notifications Hub Python SDK", "OCR", "OSS", "PKI", "POM", "Public Key Infrastructure", "PyPI", "QnA Maker REST API", "QnA Maker service", "RA-GRS", "RDP", "Remote Desktop Protocol", "Resource Manager template", "Roobo device", "Route Service SDK", "RxJava", "SPA", "SQL Data Warehouse", "SQL Database Machine Learning Services", "SSML", "SaaS", "SaaS", "SentimentAnalysis", "Service Fabric", "Service Fabric cluster", "Spark", "Speech Devices SDK", "Speech SDK", "Speech SDK Maven Package", "Speech SDK Maven package", "Speech Services", "Speech Services resource", "Speech Synthesis Markup Language", "Stream Analytics", "TFS", "TPM device", "Table API", "Team Explorer", "Text Analytics", "Text Analytics APIs", "Text Analytics Cognitive Service", "Text Analytics REST API", "Text Analytics SDK", "Text Analytics Service", "Time Series Insights", "Translator Speech API", "Translator Text API", "Translator Text REST API", "Translator Text resource", "Transpile JSX", "Transport Level Security", "UDF", "VNet", "VS Code", "VSTS", "Vetur", "Visual Studio", "Visual Studio Code", "Visual Studio Code editor", "Visual Studio Community", "Visual Studio Dev Essentials", "Visual Studio Enterprise", "Visual Studio IDE", "Visual Studio IntelliSense", "Visual Studio Professional", "Visual Studio Solution", "Visual Studio Tools", "Vue", "WAR", "WPF", "WSGI", "WildFly", "Xamarin", "Yeoman module generator", "ZipDeploy", "Zookeeper clusters"]

def allowlist_phrases(input_file, output_file):
    print("allowlist-phrases: Starting")

    with open(input_file, encoding='utf-8') as f_in:
        import csv
        # Output CSV has the same structure with added KeyPhrases column
        reader = csv.reader(f_in) 
     
        csv_headers = next(reader)        
        index_phrases = csv_headers.index("key_phrases")        

        with open(output_file, 'w', encoding='utf-8', newline='') as f_out:
            writer = csv.writer(f_out)
            writer.writerow(csv_headers)

            count = 1

            for row in reader:
                phrases = row[index_phrases]

                if phrases != '':
                    phrase_list = phrases.split(';')
                    keep_phrases = [phrase for phrase in phrase_list if phrase in allowlist]

                    # Append the phrases list (; separated) to the CSV row and write it.
                    row[index_phrases] = ';'.join(keep_phrases)
                    
                writer.writerow(row)

    print("allowlist_phrases: Completed")

if __name__ == "__main__":    
    if len(sys.argv) == 1:
        print("Usage: python allowlist_phrases.py <input_csv_file.csv>")
        print("<input_csv_file.csv> is the output from extract_key_phrases.py")
        sys.exit(2)

    # Making the output filename assumes the input filename has only one .
    input_file = sys.argv[1]
    elements = input_file.split('.')
    output_file = elements[0] + '-allowlist.' + elements[1]

    allowlist_phrases(input_file, output_file)
