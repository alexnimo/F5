#!/usr/bin/python

from f5.bigip import ManagementRoot
from f5.bigip.contexts import TransactionContextManager
import os
import sys
try:
    import configparser
except ImportError:
    print("Please install configparser")
try:
    from slackclient import SlackClient
    slackinst = "true"
except ImportError:
    print("slackclient package is not installed")
    pass
    slackinst = "false"

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


def f5_cert_deployer(b_mg, b_vs_name, b_vs_ip, b_part, b_vlan, b_http_prof, b_ssl_prof, b_vs_port, sc_vars, scObj,  *args):

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
	    try:
	        modchain = api.tm.sys.file.ssl_certs.ssl_cert.load(
            name='le-chain.crt')
            modchain.sourcePath = 'file:/var/config/rest/downloads/%s' % (
            os.path.basename(chain))
            modchain.update()
        except:
            print("chain file already exists")
            pass


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
        'defaultsFrom': '/Common/client_ssl',
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
		        pass

    if sc_vars == 1:
        sc = SlackClient(scObj[0])
        sc.api_call(
            "chat.postMessage",
            channel = scObj[2],
            text = "Certificate deployment succeeded",
            user = scObj[3],
            icon_url = scObj[1]
        )
    else:
      pass



def main(*args):

    #Read configuration from config file
    config = configparser.ConfigParser()
    config.read('f5_config')
    BIGIP_USER = config.get('f5_config' , 'BIGIP_USER')
    BIGIP_PASSWORD = config.get('f5_config' , 'BIGIP_PASSWORD')
    BIGIP_MNG_IP = config.get('f5_config' , 'BIGIP_MNG_IP')
    BIGIP_VLAN = config.get('f5_config', 'BIGIP_VLAN')
    BIGIP_PARTITION = config.get('f5_config' , 'BIGIP_PARTITION')
    BIGIP_CERTBOT_VERIFICATION_VS_NAME = config.get('f5_config' , 'BIGIP_CERTBOT_VERIFICATION_VS_NAME')
    BIGIP_CERTBOT_VERIFICATION_VS_IP = config.get('f5_config' , 'BIGIP_CERTBOT_VERIFICATION_VS_IP')
    BIGIP_SSL_VS_NAME = config.get('f5_config' , 'BIGIP_SSL_VS_NAME')
    BIGIP_SSL_VS_IP = config.get('f5_config' , 'BIGIP_SSL_VS_IP')
    BIGIP_HTTP_PROFILE = config.get('f5_config' , 'BIGIP_HTTP_PROFILE')
    BIGIP_SSL_PROFILE = config.get('f5_config' , 'BIGIP_SSL_PROFILE')
    BIGIP_SSL_VS_PORT = config.get('f5_config' ,'BIGIP_SSL_VS_PORT')

    if slackinst != "false":
        sc_token = str(config.get('slack_config' , 'slack_token'))
        sc_icon = config.get('slack_config' , "slackbot_icon_url")
        sc_channel = str(config.get('slack_config' , 'slack_channel'))
        sc_user = config.get('slack_config' , 'slack_user')
        if (len(sc_token) > 1) & (len(sc_channel) > 1):
            sc_vars = 1
            scObj =[]
            scObj.append(sc_token)
	        scObj.append(sc_icon)
	        scObj.append(sc_channel)
            scObj.append(sc_user)
        else:
            sc_vars = 0



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
                   , BIGIP_HTTP_PROFILE, BIGIP_SSL_PROFILE, BIGIP_SSL_VS_PORT, sc_vars, scObj, sys_vars)


if __name__ == '__main__':
    main(sys_vars)
