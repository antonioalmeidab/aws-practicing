import boto3
DEFAULT_DELAY = 6

ec2client = boto3.client('ec2')

def getInstances(client):
    instances = []
    response = client.describe_instances()
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            print("Instance:", instance["InstanceId"])
            print("\tVolumes:")
            instances.append(instance)
            for volume in instance["BlockDeviceMappings"]:
                print("\tDevice: {0}, Volume{1}".format(volume["DeviceName"], volume["Ebs"]["VolumeId"]))

    return instances

def create_snapshot(client, volume_id):
    snapshot = client.create_snapshot(
            Description="VolumeId {0}".format(volume_id),
            VolumeId=volume_id
    )
    return snapshot

def delete_snapshot(client, snapshot_id):
    client.delete_snapshot(SnapshotId=snapshot_id)


def create_vol_from_snapshot(client, snapshot_id, availability_zone, encrypt):
    new_volume = client.create_volume(
        AvailabilityZone=availability_zone,
        SnapshotId=snapshot_id,
        Encrypted=encrypt
    )
    return new_volume

def detach_volume(client, volume_id, device_name, instance_id):
    client.detach_volume(
        VolumeId=volume_id,
        Device=device_name,
        InstanceId=instance_id
    )

def attach_volume(client, volume_id, device_name, instance_id):
    client.attach_volume(
        Device=device_name,
        InstanceId=instance_id,
        VolumeId=volume_id
    )

def delete_volume(client, volume_id):
    client.delete_volume(VolumeId=volume_id)

def wait_snapshots(waiter, *snapshots):
    snapshot_list = list(snapshots)
    waiter.wait(
        SnapshotIds=snapshot_list,
        WaiterConfig= {
            'Delay': DEFAULT_DELAY
        }
    )

def wait_volumes(waiter, *volumes):
    volume_list = list(volumes)
    waiter.wait(
        VolumeIds=volume_list,
        WaiterConfig={
            'Delay': DEFAULT_DELAY
        }
    )

def wait_instances(waiter, *instances):
    instance_list = list(instances)
    waiter.wait(
        InstanceIds=instance_list,
        WaiterConfig= {
            'Delay': DEFAULT_DELAY
        }
    )

def main():
    instances = getInstances(ec2client)

    for instance in instances:
        instance_state = instance["State"]["Name"]
        instance_id = instance["InstanceId"]
        availability_zone = instance["Placement"]["AvailabilityZone"]

        if instance_state == "terminated":
            continue
        
        print("\nStopping instance... | Instance:", instance_id)
        ec2client.stop_instances(InstanceIds=[instance_id])
        wait_instances(ec2client.get_waiter('instance_stopped'), instance_id)
        print("Instance stopped")

        for volume in instance["BlockDeviceMappings"]:
            volume_id = volume["Ebs"]["VolumeId"]
            device_name = volume["DeviceName"]

            print("Creating snapshot... | Volume:",volume_id)
            snapshot = create_snapshot(ec2client, volume_id)
            wait_snapshots(
                ec2client.get_waiter('snapshot_completed'),
                snapshot["SnapshotId"]
            )
            print("Snapshot created")

            print("Creating volume... | Snapshot:", snapshot["SnapshotId"])
            new_volume = create_vol_from_snapshot(
                ec2client,
                snapshot["SnapshotId"],
                availability_zone,
                True
            )

            print("Detaching...")
            detach_volume(ec2client, volume_id, device_name, instance_id)

            wait_volumes(
                ec2client.get_waiter('volume_available'),
                new_volume["VolumeId"],
                volume_id
            )
            print("New volume created {0} | Volume detached {1}"
                .format(new_volume["VolumeId"], volume_id))

            delete_snapshot(ec2client, snapshot["SnapshotId"])
            delete_volume(ec2client, volume_id)

            print("Attaching...\n")
            attach_volume(ec2client, new_volume["VolumeId"], device_name, instance_id)

        ec2client.start_instances(InstanceIds=[instance_id])

if __name__ == "__main__":
    main()
        


