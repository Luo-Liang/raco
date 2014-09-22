#pragma once
#include <sstream>
#include <fstream>
#include <cstdint>
#include <string>
#include <iostream>
#include <cstdlib>

void CHECK(bool cond) {
  if (!cond) {
    std::cerr << "assertion failed" << std::endl;
    exit(1);
  }
}


template< typename Tuple >
void convert2bin_withTuple( std::string fn, uint64_t burn=0, bool add_id=false) {
  std::ifstream infile(fn, std::ifstream::in);
  CHECK( infile.is_open() );// << fn << " failed to open";
  
  std::string outpath = fn+".bin";
  std::ofstream outfile(outpath, std::ios_base::out | std::ios_base::binary );
  CHECK( outfile.is_open() );// << outpath << " failed to open";
  
  int64_t linenum = 0;
  while( infile.good() ) {
    std::string line;
    std::getline( infile, line );
    if (line.length() == 0) break; // takes care of EOF

    std::istringstream iss(line);
    auto t = Tuple::fromIStream(iss);
   
    // add a sequential id to the data
    if (add_id) {
      outfile.write(&linenum, sizeof(int64_t));
    }
 
    outfile.write((char*) &(t._fields), sizeof(int64_t)*Tuple::numFields()); 
    linenum++;
  }
  infile.close();
  outfile.close();
  std::cout << "binary: " << outpath << std::endl;
  std::cout << "rows: " << linenum << std::endl;
  std::cout << "cols: " << Tuple::numFields() << std::endl;
}
