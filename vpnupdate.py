import os

from ibm_vpc import VpcV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from dotenv import load_dotenv
from ibm_cloud_sdk_core import ApiException

load_dotenv()

APIKEY=os.getenv("APIKEY")
REGION=os.getenv("REGION")

print(f"pfqpfq REGION: {REGION}")

# vpc_stuff()

def vpc_stuff():
  authenticator = IAMAuthenticator(APIKEY)
  service = VpcV1(authenticator=authenticator)
  service_url = f"https://{REGION}.iaas.cloud.ibm.com/v1"
  service.set_service_url(service_url)
  try:
      vpcs = service.list_vpcs().get_result()['vpcs']
  except ApiException as e:
      print("List VPC failed with status code " + str(e.code) + ": " + e.message)

  print(vpcs[0]["name"])
