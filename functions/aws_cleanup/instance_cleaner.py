# this program was written using python 3.6.5

# aws_cleanup by Praqma/Eficode https://github.com/Praqma/aws-cleanup (private repo)
# modified by @zanderhavgaard

from datetime import datetime, timedelta, date
from pprint import pprint
import pytz
import boto3

FILTER_CONFIG = {"keep_running": ["prod", "test"], "garbage_collect": "gc", "avoid_terminate": "keep"}
CLEANUP_CONFIG = {
    "DAYS_BEFORE_STOP": 4,
    "DAYS_BEFORE_TERMINATE": 4,
    "STOP_TAG": "Will Stop After",
    "TERMINATE_TAG": "Will Terminate After",
    "EMAIL_SOURCE": "foo@bar.io",
}


def report(message: str) -> None:
    # add messages to report
    # TODO
    print("report", message)
    pass


FMT = "%Y-%m-%d %H:%M:%S"
DAYS_BEFORE_STOP = CLEANUP_CONFIG["DAYS_BEFORE_STOP"]
DAYS_BEFORE_TERMINATE = CLEANUP_CONFIG["DAYS_BEFORE_TERMINATE"]


class DailyInstanceClean:
    def __init__(self):
        # set profile to lambdaCD on dev machine
        # boto3.setup_default_session(profile_name='lambdaCD')

        self.regions = get_all_regions()

        # set configuration attributes as class variables
        for k, v in FILTER_CONFIG.items():
            setattr(self, k, v)


def cleanup(aws_key: str, aws_secret: str, dry_run: bool) -> dict:
    # list of dicts containing messages for each region
    cleanup_report = {"Dry run": dry_run, "region_reports": []}

    # get regions
    clean = DailyInstanceClean()

    # clean each region
    for region in clean.regions:
        stop_list = []
        terminate_list = []

        try:
            ec2 = boto3.resource("ec2", region_name=region)
            instances = ec2.instances.all()
            for instance in instances:
                if instance.state["Name"] == "running":
                    if instance.tags != None:
                        if any(tag["Key"].lower() == "status" for tag in instance.tags):
                            for tag in instance.tags:
                                if "status" in tag["Key"].lower():
                                    status = tag["Value"].lower()
                                    if any(status == key_words for key_words in clean.keep_running):
                                        report(instance.id + " is following protocol - it will continue running")
                                    elif status == clean.garbage_collect:
                                        lookup_maintainer(instance, region)
                                        report("GC activated - stopping instance " + instance.id)
                                        stop_list.append(instance.id)
                                    else:
                                        lookup_maintainer(instance, region)
                                        report("stopping instance " + instance.id)
                                        stop_list.append(instance.id)
                        else:
                            # no status tag - stopping instance
                            lookup_maintainer(instance, region)
                            report("Mising status tag - stopping instance " + instance.id)
                            stop_list.append(instance.id)

                    else:
                        # no tags - stopping instance
                        report("No tags - stopping instance " + instance.id)
                        stop_list.append(instance.id)
                else:
                    # instance not running
                    report("instance " + instance.id + " not running")

            if len(stop_list) != 0:
                report("{} number of instances will be stopped".format(len(stop_list)))
                pass
                #  ec2.instances.filter(InstanceIds=stop_list).stop()
            else:
                report("nothing to stop")

            if len(terminate_list) != 0:
                pass
                #  ec2.instance.filter(InstanceIds=terminate_list).terminate()
            else:
                report("nothing to terminate")
        except Exception as e:
            report(e)

        # dict with data for each region to be reported back to invoker
        cleanup_report["region_reports"].append(
            {"Region": region, "stop_list": stop_list, "terminate_list": terminate_list}
        )

    # TODO fix
    return cleanup_report

    #  prune_long_running_instances()


def lookup_maintainer(instance, region):
    if any(tag["Key"].lower() == "maintainer" for tag in instance.tags):
        for t in instance.tags:
            if "maintainer" in t["Key"].lower():
                maintainer = t["key"]
                print("maintainer", maintainer, region, instance.id)
                # TODO translate sending emails to adding to JSON report
                #  send_email(t["Value"], region, instance.id)


def prune_long_running_instances():
    clean = DailyInstanceClean()
    utc = pytz.UTC

    STOP_TAG = CLEANUP_CONFIG["STOP_TAG"]
    TERMINATE_TAG = CLEANUP_CONFIG["TERMINATE_TAG"]

    for region in clean.regions:
        stop_list = []
        terminate_list = []
        tag_to_stop_list = []
        tag_to_terminate_list = []
        ignore_list = []
        report(" ")
        report("---- " + region + " ----")
        try:
            ec2 = boto3.resource("ec2", region_name=region)
            instances = ec2.instances.all()
            for instance in instances:
                if instance.tags is not None:
                    # Check instances for termination
                    if any(tag["Key"] == TERMINATE_TAG for tag in instance.tags):
                        # Instance tagged to be terminated
                        date_tag = [
                            tag_dict["Value"] for tag_dict in instance.tags if tag_dict["Key"] == TERMINATE_TAG
                        ][0]
                        if is_outside_timeframe(date_tag, DAYS_BEFORE_TERMINATE):
                            # The timeframe expired -> terminate it
                            terminate_list.append(instance.id)
                        else:
                            # The timeframe hasn't expired yet -> keep it stopped for now
                            ignore_list.append(instance.id)
                    elif any(tag["Key"] == STOP_TAG for tag in instance.tags):
                        # Instance has been tagged to be stopped
                        date_tag = [tag_dict["Value"] for tag_dict in instance.tags if tag_dict["Key"] == STOP_TAG][0]
                        if is_outside_timeframe(date_tag, DAYS_BEFORE_STOP):
                            # The timeframe expired -> stop it -> mark to terminate
                            tag_to_terminate_list.append(instance.id)
                            stop_list.append(instance.id)
                        else:
                            # The timeframe hasn't expired yet -> keep it running for now
                            ignore_list.append(instance.id)
                    else:
                        # Instances is not tagged with either STOP/TERMINATE -> tag to stop
                        tag_to_stop_list.append(instance.id)
                else:
                    # No tags whatsoever -> terminate the instance immediately
                    terminate_list.append(instance.id)

            # Skip the actions and stats reporting if there are no instances to assess.
            instances_assessed = len(list(instances))
            if instances_assessed == 0:
                report("No instances are running in this region.")
            else:
                # Handle instances per region
                report("{} instances assessed:".format(instances_assessed))

                # Stop instances
                if len(stop_list) != 0:
                    report("[Dry-run] Stopping {} instances: ".format(len(stop_list)) + str(stop_list))
                    # Dry-run: Uncomment this line to stop instances
                    # ec2.instances.filter(InstanceIds=stop_list).stop()
                else:
                    report("Nothing to stop.")

                # Terminate instances
                if len(terminate_list) != 0:
                    report("[Dry-run] Terminating {} instances: ".format(len(terminate_list)) + str(terminate_list))
                    # Dry-run: Uncomment this line to terminate instances
                    # ec2.instances.filter(InstanceIds=stop_list).terminate()
                else:
                    report("Nothing to terminate.")

                # Tag instances to stop
                if len(tag_to_stop_list) != 0:
                    report("Tagging {} instances for stopping: ".format(len(tag_to_stop_list)) + str(tag_to_stop_list))
                    ec2.create_tags(Resources=tag_to_stop_list, Tags=[{"Key": STOP_TAG, "Value": get_datetime_stamp()}])
                else:
                    report("No instance were tagged for stopping.")

                # Tag instances to terminate
                if len(tag_to_terminate_list) != 0:
                    report(
                        "Tagging {} instances for termination: ".format(len(tag_to_terminate_list))
                        + str(tag_to_terminate_list)
                    )
                    ec2.create_tags(
                        Resources=tag_to_terminate_list, Tags=[{"Key": TERMINATE_TAG, "Value": get_datetime_stamp()}]
                    )
                else:
                    report("No instances were tagged for termination.")

                ignored_instances = len(ignore_list)
                if ignored_instances != 0:
                    report(
                        "{} instances have already been tagged for stopping or termination.".format(ignored_instances)
                    )

        except Exception as e:
            report("[!] Exception:" + str(e))


# Returns a list of all available EC2 regions
def get_all_regions():
    client = boto3.client("ec2")
    regions = [region["RegionName"] for region in client.describe_regions()["Regions"]]
    return regions


# This method is given a date and a day param as integer
# Returns the truth value of today being in the date period
def is_outside_timeframe(date_string, days_count):
    date_object = datetime.strptime(date_string, FMT)
    time_delta = datetime.now() - date_object
    return time_delta.days >= days_count


def describe_tags(tag):
    if tag is "stop":
        return "Instance will be stopped in {} days.".format(DAYS_BEFORE_STOP)
    elif tag is "terminate":
        return "Instance will be terminated in {} days".format(DAYS_BEFORE_TERMINATE)


def get_datetime_stamp():
    return datetime.now().strftime(FMT)
