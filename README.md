# stupidlb #

Stupid load balancer operator implementation for kubernetes.  That is
"stupid" as meaning "naive" or "simple-minded" - not incorrect.

This will assign IP addresses to Services of type LoadBalancer from a
configured set of IP ranges. That's it.

It will NOT actually update any nearby routers/firewalls, set up any
EKS/AKS/GCP resources or anything. Neither will it do anything with
BGP, OSPF or any other dynamic routing protocol.

The main use case is where:

 * You have a kubernetes cluster, with all nodes on the same subnet
 
 * You want to expose services on IP addresses in the same subnet

Here you would dedicate a range of IP addresses (which does not
conflict with the nodes themselves nor any DHCP-assigned addresses)
for load balancers.

Basically: it is useful for very simple on-prem setups where you do
not have much networking infrastructure available - e.g. for personal
k8s clusters on your home network.

The code in this repo has two main parts:

 * The `/docker` subdirectory with everything needed to create a
   docker image
   
 * The `/stupidlb` subdirectory which contains a Helm chart for
   installing the operator.
