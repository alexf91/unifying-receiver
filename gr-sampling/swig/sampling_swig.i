/* -*- c++ -*- */

#define SAMPLING_API

%include "gnuradio.i"			// the common stuff

//load generated python docstrings
%include "sampling_swig_doc.i"

%{
#include "sampling/symbol_recovery.h"
%}


%include "sampling/symbol_recovery.h"
GR_SWIG_BLOCK_MAGIC2(sampling, symbol_recovery);
