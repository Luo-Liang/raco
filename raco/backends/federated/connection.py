#from multiprocessing import Pool  # need to have GAE support it

from raco.backends.federated.algebra import FederatedAlgebra
#from raco.backends.federated.algebra import ExportMyriaToScidb
from raco.algebra import Sequence
from raco.backends.logical import OptLogicalAlgebra
from algebra import FederatedSequence, FederatedParallel, FederatedMove, FederatedExec

import logging
import numpy as np
import time

from raco.backends.myria.connection import MyriaConnection
from raco.backends.scidb.connection import SciDBConnection
from raco.backends.federated.catalog import FederatedCatalog
from raco.backends.myria.catalog import MyriaCatalog
from raco.backends.scidb.catalog import SciDBCatalog
from raco.backends.myria.myria import MyriaLeftDeepTreeAlgebra
from raco.backends.scidb.algebra import SciDBAFLAlgebra

import raco.myrial.parser as myrialparser
import raco.myrial.interpreter as interpreter

insert_loads = """
------------------------------------------------------------------------------------
-- Import from SciDB
------------------------------------------------------------------------------------
symbols0x1 = load("file:///home/gridsan/bhaynes/out/0/transform_1", csv(schema(id:int, index:int, value:int)));
symbols1x1 = load("file:///home/gridsan/bhaynes/out/1/transform_1", csv(schema(id:int, index:int, value:int)));
symbols0x2 = load("file:///home/gridsan/bhaynes/out/0/transform_2", csv(schema(id:int, index:int, value:int)));
symbols1x2 = load("file:///home/gridsan/bhaynes/out/1/transform_2", csv(schema(id:int, index:int, value:int)));
symbols0x3 = load("file:///home/gridsan/bhaynes/out/0/transform_3", csv(schema(id:int, index:int, value:int)));
symbols1x3 = load("file:///home/gridsan/bhaynes/out/1/transform_3", csv(schema(id:int, index:int, value:int)));
symbols0x4 = load("file:///home/gridsan/bhaynes/out/0/transform_4", csv(schema(id:int, index:int, value:int)));
symbols1x4 = load("file:///home/gridsan/bhaynes/out/1/transform_4", csv(schema(id:int, index:int, value:int)));
symbols0x5 = load("file:///home/gridsan/bhaynes/out/0/transform_5", csv(schema(id:int, index:int, value:int)));
symbols1x5 = load("file:///home/gridsan/bhaynes/out/1/transform_5", csv(schema(id:int, index:int, value:int)));
symbols0x6 = load("file:///home/gridsan/bhaynes/out/0/transform_6", csv(schema(id:int, index:int, value:int)));
symbols1x6 = load("file:///home/gridsan/bhaynes/out/1/transform_6", csv(schema(id:int, index:int, value:int)));
symbols0x7 = load("file:///home/gridsan/bhaynes/out/0/transform_7", csv(schema(id:int, index:int, value:int)));
symbols1x7 = load("file:///home/gridsan/bhaynes/out/1/transform_7", csv(schema(id:int, index:int, value:int)));
symbols0x8 = load("file:///home/gridsan/bhaynes/out/0/transform_8", csv(schema(id:int, index:int, value:int)));
symbols1x8 = load("file:///home/gridsan/bhaynes/out/1/transform_8", csv(schema(id:int, index:int, value:int)));

--symbols2x1 = load("file:///home/gridsan/bhaynes/out/2/transform_1", csv(schema(id:int, index:int, value:int)));
--symbols3x1 = load("file:///home/gridsan/bhaynes/out/3/transform_1", csv(schema(id:int, index:int, value:int)));
--symbols2x2 = load("file:///home/gridsan/bhaynes/out/2/transform_2", csv(schema(id:int, index:int, value:int)));
--symbols3x2 = load("file:///home/gridsan/bhaynes/out/3/transform_2", csv(schema(id:int, index:int, value:int)));
--symbols2x3 = load("file:///home/gridsan/bhaynes/out/2/transform_3", csv(schema(id:int, index:int, value:int)));
--symbols3x3 = load("file:///home/gridsan/bhaynes/out/3/transform_3", csv(schema(id:int, index:int, value:int)));
--symbols2x4 = load("file:///home/gridsan/bhaynes/out/2/transform_4", csv(schema(id:int, index:int, value:int)));
--symbols3x4 = load("file:///home/gridsan/bhaynes/out/3/transform_4", csv(schema(id:int, index:int, value:int)));
--symbols2x5 = load("file:///home/gridsan/bhaynes/out/2/transform_5", csv(schema(id:int, index:int, value:int)));
--symbols3x5 = load("file:///home/gridsan/bhaynes/out/3/transform_5", csv(schema(id:int, index:int, value:int)));
--symbols2x6 = load("file:///home/gridsan/bhaynes/out/2/transform_6", csv(schema(id:int, index:int, value:int)));
--symbols3x6 = load("file:///home/gridsan/bhaynes/out/3/transform_6", csv(schema(id:int, index:int, value:int)));
--symbols2x7 = load("file:///home/gridsan/bhaynes/out/2/transform_7", csv(schema(id:int, index:int, value:int)));
--symbols3x7 = load("file:///home/gridsan/bhaynes/out/3/transform_7", csv(schema(id:int, index:int, value:int)));
--symbols2x8 = load("file:///home/gridsan/bhaynes/out/2/transform_8", csv(schema(id:int, index:int, value:int)));
--symbols3x8 = load("file:///home/gridsan/bhaynes/out/3/transform_8", csv(schema(id:int, index:int, value:int)));

symbols = symbols0x1 + symbols0x2 + symbols0x3 + symbols0x4 +
          symbols0x5 + symbols0x6 + symbols0x7 + symbols0x8 +
          symbols1x1 + symbols1x2 + symbols1x3 + symbols1x4 +
          symbols1x5 + symbols1x6 + symbols1x7 + symbols1x8
          ;
--          +
--          symbols2x1 + symbols2x2 + symbols2x3 + symbols2x4 +
--          symbols2x5 + symbols2x6 + symbols2x7 + symbols2x8 +
--          symbols3x1 + symbols3x2 + symbols3x3 + symbols3x4 +
--          symbols3x5 + symbols3x6 + symbols3x7 + symbols3x8;
store(symbols, symbols);
symbols = scan(symbols);
"""#.format(path_prefix = 'state/partition1/scidb-bhaynes/data/000') # FOR scidb on txe1.
# """.format(path_prefix = 'home/scidb')  # FOR scidb on ec2.


__all__ = ['FederatedConnection']


class FederatedConnection(object):
    """Federates a collection of connections"""

    def __init__(self,
                 connections,
                 movers=[]):
        """
        Args:
            connections: A list of connection objects
            movers: a list of data movement strategies
        """
        self.connections = connections
        self.movers = {(strategy.source_type, strategy.target_type): strategy for strategy in movers}

    def get_myria_connection(self):
        for c in self.connections:
            if isinstance(c, MyriaConnection):
                return c

    def get_scidb_connection(self):
        for c in self.connections:
            if isinstance(c, SciDBConnection):
                return c

    def workers(self):
        """Return a dictionary of the workers"""
        raise NotImplemented

    def workers_alive(self):
        """Return a list of the workers that are alive"""
        raise NotImplemented

    def worker(self, worker_id):
        """Return information about the specified worker"""
        raise NotImplemented

    def datasets(self):
        """Return a list of the datasets that exist"""
        return sum([conn.datasets for conn in self.connections], [])

    def dataset(self, name):
        """Return information about the specified entity"""
        rel = None
        for conn in self.connections:
            try:
                rel = conn.dataset(relation_key)
            except:
                continue
            break
        if rel:
            return rel
        else:
            raise ValueError("Relation {} not found".format(relation_key))

    def download_dataset(self, relation_key):
        """Download the data in the dataset as json"""
        raise NotImplemented

    def submit_query(self, query):
        """Submit the query and return the status including the URL
        to be polled.

        Args:
            query: a Federated physical plan as a Python object.
        """
        raise NotImplemented

    def execute_query(self, query):
        """Submit the query and block until it finishes

        Args:
            query: a physical plan as a Python object.
        """

        # #TODO: Fix hack, assuming query is a query string and not a parsed plan
        # if query.split('\n', 1)[0] == "-- exec scidb":
        #     query = query.split('\n', 1)[1]
        #     return self.get_scidb_connection().execute_afl(query)
        #
        # [scidb_query, myria_query] = query.split('-- Myria')
        #
        # # print scidb_query
        # # print "-------------------SPLIT---------------"
        #
        # myria_query = insert_loads + "\n" + myria_query
        # # print myria_query
        #
        # def run_scidb():
        #     parser = myrialparser.Parser()
        #     catalog = FederatedCatalog([MyriaCatalog(self.get_myria_connection()), SciDBCatalog(self.get_scidb_connection())])
        #     processor = interpreter.StatementProcessor(catalog, False)
        #     statement_list = parser.parse(scidb_query)
        #     processor.evaluate(statement_list)
        #     algebras = [MyriaLeftDeepTreeAlgebra(), SciDBAFLAlgebra()]
        #     falg = FederatedAlgebra(algebras, catalog)
        #
        #     pd = processor.get_physical_plan(target_alg=falg)
        #
        #     # Execute SciDB Query: UNCOMMENT
        #     self.get_scidb_connection().execute_query(pd)
        #
        # run_scidb()
        # def run_myria():
        #     parser = myrialparser.Parser()
        #     processor = interpreter.StatementProcessor(MyriaCatalog(self.get_myria_connection()), False)
        #     # Start the myria execution now.
        #     statement_list = parser.parse(myria_query)
        #     processor.evaluate(statement_list)
        #     # pd = processor.get_physical_plan(target_alg=MyriaLeftDeepTreeAlgebra())
        #     # print processor.get_logical_plan()
        #
        #     r = self.get_myria_connection().execute_query(processor.get_logical_plan())
        #     r['query_status'] = r['status']
        #     r['query_url'] = r['url']
        #     # print r
        #     return r
        #
        # return run_myria()


        if isinstance(query, FederatedSequence):
            # execute each statement in the sequence, and return
            # only the result of the last statement
            return map(self.execute_query, query.args)[-1] if query.args else None
        elif isinstance(query, FederatedParallel):
            # TODO which one to return?
            raise NotImplementedError("Not supporting FedParallel in GAE")
            return Pool(len(query.args)).map(self.execute_query, query.args)
        elif isinstance(query, FederatedMove) and self._is_supported_move(query):
            return self._get_move_strategy(query).move(query)
        elif isinstance(query, FederatedExec) and self._is_supported_catalog(query):
            r = query.catalog.connection.execute_query(Sequence([query.plan]))

            #TODO fix this API mismatch more elegantly; MyriaX returns 'status' and 'url'
            if 'status' in r:
                r['query_status'] = r['status']
            if 'url' in r:
                r['query_url'] = r['url']
            return r

        elif isinstance(query, FederatedExec):
            raise LookupError("Connection of type {} not part of this federated system.".format(type(query.catalog.connection)))
        elif isinstance(query, FederatedMove):
            raise LookupError("No movement strategy exists between systems of type {} and {}".format(
                type(query.sourcecatalog.connection), type(query.targetcatalog.connection)))
        else:
            raise RuntimeError("Unsupported federated operator {}".format(type(query)))

        # def run(logical_plan, myria_conn, scidb_conn_factory):

        seq_op = federated_plan

        assert isinstance(seq_op, Sequence)

        '''
        outs = []
        pure_myria_query = all([isinstance(x, RunMyria) for x in seq_op.args])

        logging.info("Running federated query: pure_myira=%s" % pure_myria_query)

        # TODO: Assuming each phys operator carries connection info.  Is this what we want?
        for op in seq_op.args:
            if isinstance(op, RunAQL):
                logging.info("Running scidb query: %s" % op.command)
                sdb = scidb_conn_factory.connect(op.connection)
                try:
                    sdb._execute_query(op.command)
                except Exception as ex:
                    logging.info("SciDB query failure: " + str(ex))
            elif isinstance(op, RunMyria):
                logging.info("Running myria query...")

                res = myria_conn.submit_query(op.command)
                _id = res['queryId']
                if not pure_myria_query:
                    outs.append(wait_for_completion(myria_conn, _id))
                else:
                    return res
            elif isinstance(op, ExportMyriaToScidb):
                logging.info("Exporting to scidb...")

                # Download Myria data -- assumes query has completed
                relk = op.myria_relkey
                key = {'userName': relk.user, 'programName': relk.program,
                       'relationName': relk.relation}
                dataset = myria_conn.download_dataset(key)

                logging.info("Finished myria download; starting scidb upload")

                # Unpack first result
                vals = [v for row in dataset for v in row.values()]
                val0 = vals[0]

                # Store as scidb array
                sdb = scidb_conn_factory.connect(op.connection)
                try:
                    sdb.query("remove(%s)" % op.scidb_array_name)
                except:
                    pass

                sdb.query("store(build(<RecordName:int64>[i=0:0,1,0], %d), %s)" % (
                                val0, op.scidb_array_name))

          '''
    def validate_query(self, query):
        """Submit the query to Myria for validation only.

        Args:
            query: a Myria physical plan as a Python object.
        """
        raise NotImplemented

    def get_query_status(self, query_id):
        """Get the status of a submitted query.

        Args:
            query_id: the id of a submitted query
        """
        raise NotImplemented

    def get_query_plan(self, query_id, subquery_id):
        """Get the saved execution plan for a submitted query.

        Args:
            query_id: the id of a submitted query
            subquery_id: the subquery id within the specified query
        """
        raise NotImplemented

    def get_sent_logs(self, query_id, fragment_id=None):
        """Get the logs for where data was sent.

        Args:
            query_id: the id of a submitted query
            fragment_id: the id of a fragment
        """
        raise NotImplemented

    def get_profiling_log(self, query_id, fragment_id=None):
        """Get the logs for operators.

        Args:
            query_id: the id of a submitted query
            fragment_id: the id of a fragment
        """
        raise NotImplemented

    def get_profiling_log_roots(self, query_id, fragment_id):
        """Get the logs for root operators.

        Args:
            query_id: the id of a submitted query
            fragment_id: the id of a fragment
        """
        raise NotImplemented

    def queries(self, limit=None, max_id=None, min_id=None, q=None):
        """Get count and information about all submitted queries.

        Args:
            limit: the maximum number of query status results to return.
            max_id: the maximum query ID to return.
            min_id: the minimum query ID to return. Ignored if max_id is
                    present.
            q: a text search for the raw query string.
        """
        raise NotImplemented

    def upload_file(self, relation_key, schema, data, overwrite=None,
                    delimiter=None, binary=None, is_little_endian=None):
        """Upload a file in a streaming manner to Myria.

        Args:
            relation_key: relation to be created.
            schema: schema of the relation.
            data: the bytes to be uploaded.
            overwrite: optional boolean indicating that an existing relation
                should be overwritten. Myria default is False.
            delimiter: optional character which delimits a CSV file. Only valid
                if binary is False. Myria default is ','.
            binary: optional boolean indicating that the data is encoded as
                a packed binary. Myria default is False.
            is_little_endian: optional boolean indicating that the binary data
                is in little-Endian. Myria default is False.
        """
        raise NotImplemented

    def _get_move_strategy(self, query):
        return self.movers[(type(query.sourcecatalog.connection),
                type(query.targetcatalog.connection))]

    def _is_supported_move(self, query):
        return (type(query.sourcecatalog.connection),
                type(query.targetcatalog.connection)) in self.movers

    def _is_supported_catalog(self, query):
        return query.catalog.connection in self.connections