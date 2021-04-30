import os

from ibm_vpc import VpcV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from dotenv import load_dotenv
from ibm_cloud_sdk_core import ApiException
import typer
from fastapi import FastAPI
fastapi_app = FastAPI()

import pprint
import sys

load_dotenv()

def debug_print():
  pp = pprint.PrettyPrinter(indent=2)
  print("-- os.environ:")
  pp.pprint(dict(os.environ))
  print("-- sys.argv:")
  pp.pprint(sys.argv)
  print("-- end")

# debug_print()

APIKEY=os.getenv("APIKEY")
REGION=os.getenv("REGION")
VPN_GATEWAY_ID=os.getenv("VPN_GATEWAY_ID")
VPC_ID=os.getenv("VPC_ID")
ROUTING_TABLE_ID=os.getenv("ROUTING_TABLE_ID")
ZONE=os.getenv("ZONE")
ENTERPRISE_CIDR=os.getenv("ENTERPRISE_CIDR")
ROUTE_NAME=os.getenv("ROUTE_NAME")

authenticator = IAMAuthenticator(APIKEY)
service = VpcV1(authenticator=authenticator)
service_url = f"https://{REGION}.iaas.cloud.ibm.com/v1"
service.set_service_url(service_url)

def vpn_member(vpn_gateway_id, role):
  response = service.get_vpn_gateway(vpn_gateway_id)
  for member in response.result["members"]:
    if member["role"] == role:
      return member
  return None

def vpn_active_available_private_ip(vpn_gateway_id):
  member = vpn_member(vpn_gateway_id, "active")
  if member and member["status"] == "available":
    return member["private_ip"]["address"]
  return None

def vpn_standby_ip(vpn_gateway_id):
  member = vpn_member(vpn_gateway_id, "standby")
  if member:
    return member["private_ip"]["address"]
  return None

def transit_gateway_ingress_routing_table(service, vpc_id, routing_table_id):
  routing_table_collection = service.list_vpc_routing_tables(vpc_id=vpc_id).get_result()
  for routing_table in routing_table_collection["routing_tables"]:
    if routing_table['id'] == routing_table_id:
      return routing_table
  return None

def fix_up_routing_table_route(private_ip):
  routing_table = transit_gateway_ingress_routing_table(service, VPC_ID, ROUTING_TABLE_ID)
  if not routing_table:
    print("routing table not found")
    return
  if not routing_table['route_transit_gateway_ingress']:
    print("misconfigured routing table, it is not a transit gateway ingress table")
    return
  list_vpc_routing_table_routes_response = service.list_vpc_routing_table_routes(VPC_ID, ROUTING_TABLE_ID)
  route_collection = list_vpc_routing_table_routes_response.get_result()
  routes = route_collection["routes"]
  if len(routes) > 1:
    print(f"expecting zero or one route in the vpc routing table got {len(routes)}")
    return
  elif len(routes) == 0:
    print(f"there are zero routes, creating a new route next hop: {private_ip}")
    zone_identity_model = {'name': ZONE}
    route_next_hop_prototype_model = {"address": private_ip}
    create_vpc_routing_table_route_response = service.create_vpc_routing_table_route(
      VPC_ID,
      ROUTING_TABLE_ID,
      destination=ENTERPRISE_CIDR,
      zone=zone_identity_model,
      action='deliver',
      next_hop=route_next_hop_prototype_model,
      name=ROUTE_NAME)
    if create_vpc_routing_table_route_response.status_code != 201:
      print("vpc route table route create failed expecting status code 201 got {create_vpc_routing_table_route_response.status_code}")
      return
    route = create_vpc_routing_table_route_response.get_result()
    return

  route = routes[0]
  if route["lifecycle_state"] != "stable":
    print("vpc route table route is not lifecycle stable")
    return
  if route["action"] != "deliver":
    print("vpc route table route is not action deliver")
    return
  if "address" not in route["next_hop"] or route["next_hop"]["address"] != private_ip:
    print("fix required deleting route")
    delete_vpc_routing_table_route_response = service.delete_vpc_routing_table_route(VPC_ID, ROUTING_TABLE_ID, route["id"])
    if delete_vpc_routing_table_route_response.status_code != 204:
      print("vpc route table route delete failed expecting status code 204 got {delete_vpc_routing_table_route_response.status_code}")
    # todo consider waiting for this route to be deleted and create a new route.  Instead waiting for the next timer
    return
  print("everything looks good - nothing to fix")

def fix_action():
  private_available_ip = vpn_active_available_private_ip(VPN_GATEWAY_ID)
  if private_available_ip:
    fix_up_routing_table_route(private_available_ip)
  else:
    print("searched vpn for active available members and none were found")

def unfix_action():
  private_standby_ip = vpn_standby_ip(VPN_GATEWAY_ID)
  if private_standby_ip:
    fix_up_routing_table_route(private_standby_ip)
  else:
    print("no private standby ip")

@fastapi_app.get("/")
async def root():
  fix_action()

app = typer.Typer()

@app.command("fix")
def fix_command():
    fix_action()

@app.command("unfix")
def unfix_command():
    unfix_action()


if __name__ == "__main__":
    app()
