#!/usr/bin/python

from f5.bigip import ManagementRoot
from f5.bigip.contexts import TransactionContextManager
import os
import sys



#################Global Variables###############

#BIGIP USER
BIGIP_USER = "admin"

#BIGIP Password
BIGIP_PASSWORD = "admin"

#BIGIP Management IP Address
BIGIP_MNG_IP = ""

#BIGIP default partition
BIGIP_PARTITION ="Common"

#BIGIP Certbot HTTP VS NAME ( certbot HTTP verification)
BIGIP_CERTBOT_VERIFICATION_VS_NAME = "certbot_challenge"

#BIGIP CERTBOT HTTP VS IP ( certbot HTTP verification VS IP)
BIGIP_CERTBOT_VERIFICATION_VS_IP = ""

#BIGIP SSL/TLS VS NAME (Actual VS Name to attach SSL profile)
BIGIP_SSL_VS_NAME = "Main_VS"

#BIGIP SSL VS NAME (Actual VS IP to attach SSL profile)
BIGIP_SSL_VS_IP = ""

#BIGIP Vlan
BIGIP_VLAN =""

#HTTP profile to use with the SSL VS
BIGIP_HTTP_PROFILE ="http"

#BIGIP SSL Profile with generated certificates
BIGIP_SSL_PROFILE = "certbot_client_ssl"

#BIGIP VS Default SSL PORT
BIGIP_SSL_VS_PORT = "443"
#########################

sys_vars = sys.argv

def deploy_challenge(b_mg,  b_vs_name, b_vs_ip, b_part, b_vlan, *args):

    print("Deploying challenge irule and VS on Big_IP")
    chl_irule = """when HTTP_REQUEST { \n \
                if { [HTTP::path] starts_with \"/.well-known/acme-challenge/\" } { \n \
                 HTTP::respond 200 content {""" + str(args[0][4]) + """} } }"""

    try:
        if not(b_mg.tm.ltm.virtuals.virtual.exists(name = b_vs_name , partition = b_part )):
            b_mg.tm.ltm.rules.rule.create(name="acme_challenge", apiAnonymous=chl_irule, partition=b_part)
            b_mg.tm.ltm.virtuals.virtual.create(name = b_vs_name , partition = b_part, destination = b_vs_ip + ':80'
                                                , sourceAddressTranslation = {'type' : 'automap'} ,mask = '255.255.255.255'
                                                 , vlans = [b_vlan], rules = ['acme_challenge'], profiles = [{'name' : 'http'} ])

        else:
            b_mg.tm.ltm.rules.rule.create(name = "acme_challenge", apiAnonymous = chl_irule, partition = b_part)
            vs = b_mg.tm.ltm.virtuals.virtual.load(name = b_vs_name, partition = b_part)
            vs.rules.append("acme_challenge")
            vs.update()

    except Exception as err:
        print(err)

def clean_challenge(b_mg, b_vs_name, b_part):
    vs = b_mg.tm.ltm.virtuals.virtual.load(name = b_vs_name, partition = b_part)
    vs.delete()
    rule = b_mg.tm.ltm.rules.rule.load(name = "acme_challenge", partition = b_part)
    rule.delete()


def f5_cert_deployer(b_mg, b_vs_name, b_vs_ip, b_part, b_vlan, b_http_prof, b_ssl_prof, b_vs_port, *args):

    domain = args[0][2]
    key = args[0][3]
    cert = args[0][4]
    chain = args[0][5]


    # Upload files
    b_mg.shared.file_transfer.uploads.upload_file(key)
    b_mg.shared.file_transfer.uploads.upload_file(cert)
    b_mg.shared.file_transfer.uploads.upload_file(chain)


    # Check to see if these already exist
    key_status = b_mg.tm.sys.file.ssl_keys.ssl_key.exists(
        name=domain + ".key")
    cert_status = b_mg.tm.sys.file.ssl_certs.ssl_cert.exists(
        name=domain + ".crt")
    chain_status = b_mg.tm.sys.file.ssl_certs.ssl_cert.exists(name='le-chain.crt')

    if key_status and cert_status and chain_status:


        # Because they exist, we will modify them in a transaction
        tx = b_mg.tm.transactions.transaction
        with TransactionContextManager(tx) as api:

            modkey = api.tm.sys.file.ssl_keys.ssl_key.load(
                name=domain + ".key")
            modkey.sourcePath = 'file:/var/config/rest/downloads/%s' % (
                os.path.basename(key))
            modkey.update()

            modcert = api.tm.sys.file.ssl_certs.ssl_cert.load(
                name=domain + ".crt")
            modcert.sourcePath = 'file:/var/config/rest/downloads/%s' % (
                os.path.basename(cert))
            modcert.update()

            modchain = api.tm.sys.file.ssl_certs.ssl_cert.load(
                name='le-chain.crt')
            modchain.sourcePath = 'file:/var/config/rest/downloads/%s' % (
                os.path.basename(chain))
            modchain.update()


    else:
        newkey = b_mg.tm.sys.file.ssl_keys.ssl_key.create(
            name=domain + ".key",
            sourcePath='file:/var/config/rest/downloads/%s' % (
                os.path.basename(key)))
        newcert = b_mg.tm.sys.file.ssl_certs.ssl_cert.create(
            name=domain + ".crt",
            sourcePath='file:/var/config/rest/downloads/%s' % (
                os.path.basename(cert)))
        newchain = b_mg.tm.sys.file.ssl_certs.ssl_cert.create(
            name='le-chain.crt',
            sourcePath='file:/var/config/rest/downloads/%s' % (
                os.path.basename(chain)))

    certKeyChain = {'certKeyChain': [{
        'name': domain,
        'defaultsFrom': '/Common/lorx_client_ssl',
        'cert': "/" + b_part + "/" + domain + ".crt",
        'key': "/" + b_part + "/" + domain + ".key",
        'chain': "/" + b_part + "/le-chain.crt"}]}


    if not (b_mg.tm.ltm.virtuals.virtual.exists(name=b_vs_name, partition=b_part)):
        b_mg.tm.ltm.virtuals.virtual.create(name=b_vs_name, partition=b_part, destination=b_vs_ip + ':' + b_vs_port
                                            , sourceAddressTranslation={'type': "automap"}, mask='255.255.255.255'
                                            , vlans=[b_vlan], profiles=[{'name': b_http_prof}])
        if not (b_mg.tm.ltm.profile.client_ssls.client_ssl.exists(name=b_ssl_prof, partition=b_part)):
            b_mg.tm.ltm.profile.client_ssls.client_ssl.create(name=b_ssl_prof, partition=b_part)
            vs = b_mg.tm.ltm.virtuals.virtual.load(name=b_vs_name, partition=b_part)
            ssl_prof = b_mg.tm.ltm.profile.client_ssls.client_ssl.load(name=b_ssl_prof, partition=b_part)
            ssl_prof.modify(**certKeyChain)
            prof = vs.profiles_s.profiles.create(name=ssl_prof, partition=b_part)

        else:
            vs = b_mg.tm.ltm.virtuals.virtual.load(name=b_vs_name, partition=b_part)
            prof = vs.profiles_s.profiles.create(name=b_ssl_prof, partition=b_part)
            with TransactionContextManager(s1) as api1:
                print("attach ssl prof")
                ssl_prof = api1.tm.ltm.profile.client_ssls.client_ssl.load(name=b_ssl_prof,
                                                                           partition=b_part)
                ssl_prof.modify(**certKeyChain)
                prof = vs.profiles_s.profiles.create(name=b_ssl_prof, partition=b_part)


    else:
        if not (b_mg.tm.ltm.profile.client_ssls.client_ssl.exists(name=b_ssl_prof, partition=b_part)):
            ssl_prof = b_mg.tm.ltm.profile.client_ssls.client_ssl.create(name=b_ssl_prof, partition=b_part)
            ssl_prof.modify(**certKeyChain)
            vs = b_mg.tm.ltm.virtuals.virtual.load(name=b_vs_name, partition=b_part)
            prof = vs.profiles_s.profiles.create(name=b_ssl_prof, partition=b_part)
        else:
            try:
                #for virt in b_mg.tm.ltm.virtuals.get_collection():
                vs = b_mg.tm.ltm.virtuals.virtual.load(name=b_vs_name, partition=b_part)
                ssl_profs = vs.profiles_s.get_collection()
                for i in range(len(ssl_profs)):

                    profs_list =[]
                    profs_list = profs_list.append(ssl_profs[i].name)
                    print(ssl_profs[i].name)
                   # print(str(ssl_profs[i].name))
                    if (str(ssl_profs[i].name) == b_ssl_prof):
                        print(str(ssl_profs[i].name))
                        ssl_profs.modify(**certKeyChain)
                        break

                    else:

                        if vs.profiles_s.profiles.exists(name=b_ssl_prof, partition=b_part):
                            break

                        else:
                            s1 = b_mg.tm.transactions.transaction
                            with TransactionContextManager(s1) as api1:
                                print("else run")
                                ssl_prof = api1.tm.ltm.profile.client_ssls.client_ssl.load(name=b_ssl_prof,
                                                                                           partition=b_part)
                                ssl_prof.modify(**certKeyChain)
                                vs = api1.tm.ltm.virtuals.virtual.load(name=b_vs_name, partition=b_part)
                                prof = vs.profiles_s.profiles.create(name=b_ssl_prof, partition=b_part)

            except Exception as err:
                print(err)




def main(*args):
    mgmt = ManagementRoot(BIGIP_MNG_IP, BIGIP_USER, BIGIP_PASSWORD)
    print(args[0][1])
    ###hook logic -- arguments from the config file, passed to the hook script
    if args[0][1] == "deploy_challenge":
        deploy_challenge(mgmt, BIGIP_CERTBOT_VERIFICATION_VS_NAME, BIGIP_CERTBOT_VERIFICATION_VS_IP
                         , BIGIP_PARTITION ,BIGIP_VLAN, sys_vars)

    elif args[0][1] == "clean_challenge":
        clean_challenge(mgmt, BIGIP_CERTBOT_VERIFICATION_VS_NAME, BIGIP_PARTITION)

    elif args[0][1] == "deploy_cert":
        f5_cert_deployer( mgmt, BIGIP_SSL_VS_NAME, BIGIP_SSL_VS_IP, BIGIP_PARTITION, BIGIP_VLAN
                   , BIGIP_HTTP_PROFILE, BIGIP_SSL_PROFILE, BIGIP_SSL_VS_PORT, sys_vars)


if __name__ == '__main__':
    main(sys_vars)
