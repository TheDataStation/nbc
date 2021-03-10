## Quick Start

```shell
git clone git@github.com:TheDataStation/aurum-dod-staging.git
cd aurum-dod-staging
```

We explain next how to configure the modules to get a barebones installation. We
do this in a series of 3 stages.

### Stage 1: Configuring DDProfiler

The profiler is built in Java (you can find it under /ddprofiler). The input are
data sources (files and tables) to analyze and the output is stored in
elasticsearch. Next, you can find instructions to build and deploy the profiler as well as
to install and configure Elasticsearch.

#### Building ddprofiler

You will need JVM 8 available in the system for this step. From the root directory go to 'ddprofiler' and do:

BENC: this seems to download a super-old version of gradle which doesn't like openjdk
v11, and gives this error:

```
FAILURE: Build failed with an exception.

* What went wrong:
Could not determine java version from '11.0.9.1'.
```

There's a closed gradle issue that this was fixed by gradle 4.10.3
What was downloaded by this script was gradle 2.13.
https://github.com/gradle/gradle/issues/8671 

So is this *exactly* JVM 8, or should gradle be updated?


```shell
$> cd ddprofiler
$> bash build.sh 
```

#### Deploying Elasticsearch (tested with 6.0.0)

Download the software (note the currently supported version is 6.0.0) from:
[needs to be 6.0.0, not the latest at the time that I'm writing... the latest is 7.1.something, but that will only talk protoocl back to 6.8.0, but python requirements.txt stack uses 6.0.0 protocol]

https://www.elastic.co/products/elasticsearch

Uncompress it and then run from the root directory:

```shell
$> ./bin/elasticsearch
```

that will start the server in localhost:9200 by default, which is the address
you should use to configure ddprofiler as we show next.

#### Configuration of ddprofiler

There are two different ways of interacting with the profiler. One is through a
YAML file, which describes and configures the different data sources to profile.
The second way is through an interactive interface which we are currently
working on. We describe next the configuration of sources through the YAML file.

The jar file produced in the previous step accepts a number of flags, of which
the most relevant one is:

**--sources** Which accepts a path to a YAML file in which to configure the
access to the different data sources, e.g., folder with CSV files or
JDBC-compatible RDBMS.

You can find an example template file
[here](https://github.com/mitdbg/aurum-datadiscovery/blob/master/ddprofiler/src/main/resources/template.yml)
which contains documentation to explain how to use it. 

A typical usage of the profiler from the command line will look like:

Example:

```shell
$> bash run.sh --sources <path_to_sources.yml> 
```

You can consult all configuration parameters by appending **--help** or <?> as a
parameter. In particular you may be interested in changing the default
elasticsearch ports (consult *--store.http.port* and *--store.port*) in case
your installation does not use the default ones.

*Note that, although the YAML file accepts any number of data sources, at the
moment we recommend to profile one single source at a time.* Note, however, that
you can run ddprofiler as many times as necessary using a YAML with a different
data source. For example, if you want to index a repository of CSV files and a
RDBMS, you will need to run ddprofiler two times, each one configured to read
the data from each source. All data summaries will be created and stored in
elasticsearch. Only make sure to edit the YAML file appropriately each time.

### Stage 2: Building a Model

Once you have used the ddprofiler to create data summaries of all the data
sources you want, the second stage will read those and create a model. We
briefly explain next the requirements for running the model builder.

#### Requirements

*As typical with Python deployments, we recommend using a virtualenvironment (see
virtualenv) so that you can quickly wipeout the environment if you no longer
need it without affecting any system-wide dependencies.* 

In a Debian-based Linux system, the following packages will need to be installed system-wide:
[maybe before that requirements.txt install? in which case this stanza should be before the pip install stanza]

```shell
sudo apt-get install \
     pkg-config libpng-dev libfreetype6-dev `#(requirement of matplotlib)` \
     libblas-dev liblapack-dev `#(speeding up linear algebra operations)` \
     lib32ncurses5-dev 
  and these for compiling the python stack:
     [libpq-dev] [python3-dev]
```

Requires Python 3 (tested with 3.4, 3.5 and 3.6 [i'm using 3.7 because welcome to the future]). Use requirements.txt to
install all the dependencies:

```shell
$> pip install -r requirements.txt
```

[This fails with: ERROR: Could not find a version that satisfies the requirement pdb==0.1
- pdb==0.1 is explicitly specified in requirements.txt.

is that referring to pdb in the default python install? I've asked yue.

psycopg2 fails to install - looks like its missing some non-python pre-req. it wants pg_config as an executable - which is in libpq-dev in debian
]

[now I hit a conflict between:
   elastic-search and explicitly pinned library versions:
```
The conflict is caused by:
    The user requested urllib3==1.15.1
    elasticsearch 6.0.0 depends on urllib3<1.23 and >=1.21.1
```

Maybe i can remove that urllib3 pin?
]

[next I hit this requirements problem:
The conflict is caused by:
    The user requested elasticsearch==6.0.0
    elasticsearch-dsl 2.0.0 depends on elasticsearch<3.0.0 and >=2.0.0

remove version requirements on elasticsearch and elasticsearch-dsl? what is that going to break?

]

[
some stuff fails because it can't find Python.h - this needs, on debian, python3-dev

]

[next some stuff with readline.. which google search seems to think is terribly dated because python has better readline support built in now? (which i haven't verified...) but lets just delete the readline and gnureadline dependencies from requirements.txt]

[matplotlib needs g++]

[wtf is line-profiler needed for in requirements? it's breaking even pipgrip to explore dependencies, with what looks like a C API being out of date. delete this in an attempt to get pipgrip running. it was pinned at a crazy old version.]

[numpy version pin maybe causing conflicts too? likewise pandas. remove the version pins on both of those and scikit-learn]

Some notes for Mac users:

If you run within a virtualenvironment, Matplotlib will fail due to a mismatch with the backend it wants to use. A way of fixing this is to create a file: *~/.matplotlib/matplotlibrc* and add a single line: *backend: TkAgg*.

Note you need to use elasticsearch 6.0.0 in the current version. [exactly 6.0.0 or >=6.0.0? pretty much, exactly 6.0.0]

#### Deployment

The model builder is executed from 'networkbuildercoordinator.py', which takes
exactly two parameter, **--opath**, that expects a path to an existing folder
where you want to store the built model (in the form of Python pickle files); **--tpath**,
that expects a path to your csv files.

For example:

```shell
$> python networkbuildercoordinator.py --opath test/testmodel/network --tpath table_path
```

Once the model is built, it will be serialized and stored in the provided path.

### Stage 3: Accessing the discovery API

The file ddapi.py is the core implementation of Aurum's API. One easy way to
access it is to deserialize a desired model and constructing an API object with
that model. The easiest way to do so is by importing init_system() function from
main. Something like:

```python
from main import init_system
api, reporting = init_system(<path_to_serialized_model>, create_reporting=False)
```

The last parameter of init_system, reporting, controls whether you want to
create a reporting API that gives you access to statistics about the model. Feel
free to say yes, but beware that it may take long times when the models are big.

## Using the Discovery API

The discovery API consists of a collection of primitives that can be combined
together to write more complex data discovery queries. Consider a scenario in
which you want to identify buildings at MIT. There is a discovery primitive to
search for specific values in a column, e.g., "Stata Center". There is another
primitive to find a column with a specific schema name, e.g., "Building Name".
If you use any of them individually, you may find a lot of values, with only a
subset being relevant, e.g., many organizations may have a table that contains a
columns named "Building Name". Combining both of them makes the purpose more
specific and therefore narrows down the qualifying data, hopefully yielding
relevant results.

To use the discovery API it is useful to know about the primitives available and
about two special objects that we use to connect the primitives together and
help you navigate the results. These objects are the **API Handler** and the
**Discovery Result Set (DRS)**. We describe them both next:

**API Handler**: This is the object that you obtain when initializing the API,
that is:

```python
api, reporting = init_system(<path_to_serialized_model>, reporting=False)
```

The API Handler gives you access to the different primitives available in the
system, so it should be the first object to inspect when learning how to use the
system.

The *Discovery Result Set (DRS)* is an object that essentially represents data
within the discovery system. For example, by creating a DRS over a table in a
storage system, we are creating a reference to that table, that can be used with
the primitives. If, for example, we want to identify columns similar to a column
*A* of interest, we will need to obtain first a reference to column *A* that we
can use in the API. That reference is the DRS, and we provide several primitives
to obtain these references. Then, if we run a similarity primitive on column
*A*, the results will also be available in a DRS object --- this is what allows
to arbitrarily combine primitives together.

DRS objects have a few functions that help to inspect their content, for
example, to print the tables they represent or the columns they represent. The
more nuanced aspect of DRS is that they have an internal state that determines
whether they represent *tables* or *columns*. This is the most important aspect
to understand about the Aurum discovery API, really. We explain it in some
detail next:

Consider the *intersection* primitive, which helps in combining two DRS by
taking their intersection, e.g., similar content *and* similar schema. It is
possible to intersect at the table (tables that appear in both DRS) or column
level (columns that appear in both of them), and this can be achieved by setting
the status of the input DRS to table or column.


### Example Discovery Queries

Soon...
