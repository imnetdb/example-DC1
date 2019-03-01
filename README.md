# Example Repository

This repository contains a "toy app" that is really meant to motivate the development
of the IMNetDB library.  This "example DC1" set of files is not meant to be something to 
be used as part of a production app or any other purposes except for demonstration of
IMNetDB concepts and capabilities.  This repo is *experimental* and the code is not expected 
to be always in a working state or generally usable condition. 

# Use-Case Overview

Build a database that models the following:
   - 2 spine switches
   - 8 racks, each composed of two leaf switches
   - management of IP addresses for
      * device loopback IPs
      * leaf-spine p2p /31 interface IPs
   - management of ASN assignments
   
