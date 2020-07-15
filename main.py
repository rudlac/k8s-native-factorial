#!/usr/bin/env python

from flask import Flask
from kubernetes import client, config, watch
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--calc", type=int)
args, _ = parser.parse_known_args()

namespace = "fat"
service_account = "fat"
name = "fat-calc"
image = "fat:foo"

def calc(n):

    if n < 2:
        return 1

    else:
        config.load_incluster_config()

        core_api = client.CoreV1Api()
        batch_api = client.BatchV1Api()
        watch_api = watch.Watch()

        container = client.V1Container(
            name=name,
            image=image,
            args=["--calc", f"{n}"]
        )

        template = client.V1PodTemplateSpec(
            spec=client.V1PodSpec(restart_policy="Never", service_account_name=service_account, containers=[container])
        )

        job = client.V1Job(
            metadata=client.V1ObjectMeta(namespace=namespace, generate_name=f"{name}-"),
            spec=client.V1JobSpec(template=template, ttl_seconds_after_finished=0)
        )

        res = batch_api.create_namespaced_job(
            body=job,
            namespace=namespace,
        )

        job_name = res.metadata.name

        for event in watch_api.stream(
                func=core_api.list_namespaced_pod,
                namespace=namespace,
                label_selector=f"job-name={job_name}",
                timeout_seconds=1200
        ):
            if event["object"].status.phase == "Succeeded":
                pod_name = event["object"].metadata.name
                watch_api.stop()
                break

        if pod_name:
            log = core_api.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
            )

            val = int(log)

        batch_api.delete_namespaced_job(job_name, namespace, propagation_policy="Background")

        return val

if args.calc:

    print(args.calc * calc(args.calc - 1))

else:

    app = Flask(__name__)
    
    @app.route("/<int:n>/")
    def fat(n):
        return f"{calc(n)}"

    app.run(host="0.0.0.0")

