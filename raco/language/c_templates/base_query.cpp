// Precount_select: Use buckets to track the number of matches
// Use buckets to copy into the result array
#include <cstdio>
#include <cstdlib>     // for exit()
#include <fcntl.h>      // for open()
#include <unistd.h>     // for close()
#include <sys/stat.h>   // for fstat()
#include <ctype.h>      // for isdigit()
#include <cstring>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/file.h>

#ifdef __MTA__
#include <machine/runtime.h>
#include <luc/luc_common.h>
#include <snapshot/client.h>
#include <sys/mta_task.h>


typedef int int64;
typedef unsigned uint64;
#else
#include <sys/time.h>

#include <iomanip>
#include <cstdint>
#include <iostream>
#include <fstream>
typedef int64_t int64;
typedef uint64_t uint64;

#include <unordered_map>
#include <vector>
#include <limits>
#endif

#include "io_util.h"
#include "hash.h"
#include "utils.h"
#include "strings.h"
#include "timing.h"

// ------------------------------------------------------------------

#define Subject   0
#define Predicate 1
#define Object    2
#define Graph     3

#define XXX  330337405
#define YYY 1342785348
#define ZZZ 1395042699

#define buckets 100000

uint64_t emit_count=0;

const uint64 mask = (1L << 53) - 1;
/*
// Insert a value into a hash table
void insert(uint64 **ht1, uint64 size1, uint64 offset)
{
  uint64 hash = (uint64(offset) & mask) %% size1;
#ifdef __MTA__
  while (1) {
    if (!readff(ht1 + hash)) {
      uint64 *p = readfe(ht1 + hash); // lock it
      if (p) writeef(ht1 + hash, p); // unlock and try again
      else break;
    }
    hash++;
    if (hash == size1)
    hash = 0;
  }
  writeef(ht1 + hash, relation2 + i); // unlock it
#else
  while (ht1[hash]) {
    hash++;
    if (hash == size1) hash = 0;
  }
  ht1[hash] = relation2 + i;
#endif
}
*/


inline bool equals(struct relationInfo *left, uint64 leftrow, uint64 leftattribute
                    , struct relationInfo *right, uint64 rightrow, uint64 rightattribute) {
  /* Convenience function for evaluating equi-join conditions */
  uint64 leftval = left->relation[leftrow*left->fields + leftattribute];
  uint64 rightval = right->relation[rightrow*right->fields + rightattribute];
  return leftval == rightval;
}

{{declarations}}

StringIndex string_index;
void init( ) {
}


void query(struct relationInfo *resultInfo)
{
  printf("\nstarting Query stdout\n");fflush(stdout);

  double start = timer();

  uint64 resultcount = 0;
  struct relationInfo {{resultsym}}_val;
  struct relationInfo *{{resultsym}} = &{{resultsym}}_val;


  // -----------------------------------------------------------
  // Fill in query here
  // -----------------------------------------------------------
  {{initialized}}


 {{queryexec}}


  // return final result
  resultInfo->tuples = {{resultsym}}->tuples;
  resultInfo->fields = {{resultsym}}->fields;
  resultInfo->relation = {{resultsym}}->relation;

}



int main(int argc, char **argv) {

  struct relationInfo resultInfo;

  init();

    printf("post-init stdout\n");fflush(stdout);

  // Execute the query
  query(&resultInfo);

    printf("post-query stdout\n");fflush(stdout);

#ifdef ZAPPA
//  printrelation(&resultInfo);
#endif
//  free(resultInfo.relation);

    printf("exiting stdout\n");fflush(stdout);

}
