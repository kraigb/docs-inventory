"""A simple example how to use KustoClient."""

from datetime import timedelta
from azure.kusto.data.request import KustoClient, KustoConnectionStringBuilder, ClientRequestProperties
from azure.kusto.data.exceptions import KustoServiceError
from azure.kusto.data.helpers import dataframe_from_result_table


######################################################
##                        AUTH                      ##
######################################################
cluster = "https://cgadataout.kusto.windows.net"

# In case you want to authenticate with AAD application.
client_id = "4d689d25-8f84-43ae-b760-00fa6b4de59a"
client_secret = "ZUCNxgt_rkd_D7oz2q:Mh28.T86j:gzG"

# read more at https://docs.microsoft.com/en-us/onedrive/find-your-office-365-tenant-id
authority_id = "72f988bf-86f1-41af-91ab-2d7cd011db47"

kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
    cluster, client_id, client_secret, authority_id
)

# The authentication method will be taken from the chosen KustoConnectionStringBuilder.
client = KustoClient(kcsb)

######################################################
##                       QUERY                      ##
######################################################

# once authenticated, usage is as following
db = "CustomerTouchPoint"
query = "TopicMetadata | take 10"

response = client.execute(db, query)

# iterating over rows is possible
for row in response.primary_results[0]:
    # printing specific columns by index
    print("value at 0 {}".format(row[0]))
    print("\n")
    # printing specific columns by name
    print("EventType:{}".format(row["EventType"]))

# tables are serializeable, so:
with open("results.json", "w+") as f:
    f.write(str(response.primary_results[0]))

# we also support dataframes:
dataframe = dataframe_from_result_table(response.primary_results[0])

print(dataframe)

##################
### EXCEPTIONS ###
##################


# Query is too big to be executed
query = "StormEvents"
try:
    response = client.execute(db, query)
except KustoServiceError as error:
    print("2. Error:", error)
    print("2. Is semantic error:", error.is_semantic_error())
    print("2. Has partial results:", error.has_partial_results())
    print("2. Result size:", len(error.get_partial_results()))

properties = ClientRequestProperties()
properties.set_option(properties.OptionDeferPartialQueryFailures, True)
properties.set_option(properties.OptionServerTimeout, timedelta(seconds=8 * 60))
response = client.execute(db, query, properties=properties)
print("3. Response error count: ", response.errors_count)
print("3. Exceptions:", response.get_exceptions())
print("3. Result size:", len(response.primary_results))

# Query has semantic error
query = "StormEvents | where foo = bar"
try:
    response = client.execute(db, query)
except KustoServiceError as error:
    print("4. Error:", error)
    print("4. Is semantic error:", error.is_semantic_error())
    print("4. Has partial results:", error.has_partial_results())


client = KustoClient("https://kustolab.kusto.windows.net")
response = client.execute("ML", ".show version")

query = """
let max_t = datetime(2016-09-03);
service_traffic
| make-series num=count() on TimeStamp in range(max_t-5d, max_t, 1h) by OsVer
"""
response = client.execute_query("ML", query).primary_results[0]
