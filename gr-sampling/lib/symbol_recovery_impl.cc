/* -*- c++ -*- */
/* 
 * Copyright 2015 <+YOU OR YOUR COMPANY+>.
 * 
 * This is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 * 
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this software; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/io_signature.h>
#include "symbol_recovery_impl.h"

#include <iostream>

namespace gr {
  namespace sampling {

    symbol_recovery::sptr
    symbol_recovery::make(int samp_per_symb)
    {
      return gnuradio::get_initial_sptr
        (new symbol_recovery_impl(samp_per_symb));
    }

    /*
     * The private constructor
     */
    symbol_recovery_impl::symbol_recovery_impl(int samp_per_symb)
      : gr::block("symbol_recovery",
              gr::io_signature::make(1, 1, sizeof(char)),
              gr::io_signature::make(1, 1, sizeof(char)))
    {
        m_samp_per_symb = samp_per_symb;
        m_last = 0;
        m_counter = 0;
    }

    /*
     * Our virtual destructor.
     */
    symbol_recovery_impl::~symbol_recovery_impl()
    {
    }

    void
    symbol_recovery_impl::forecast (int noutput_items, gr_vector_int &ninput_items_required)
    {
        ninput_items_required[0] = noutput_items * m_samp_per_symb;
    }

    int
    symbol_recovery_impl::general_work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
        const char *in = (const char *) input_items[0];
        char *out = (char *) output_items[0];

        int produced = 0;
        int consumed = 0;

        while(produced < noutput_items && consumed < ninput_items[0]) {
            char bit = in[consumed];
            if(bit != m_last)
                m_counter = 0;
            m_counter++;

            if(m_counter % m_samp_per_symb == m_samp_per_symb / 2) {
                out[produced] = bit;
                produced++;
            }
            m_last = bit;
            consumed += 1;
        }

        consume_each(consumed);
        return produced;
    }

  } /* namespace sampling */
} /* namespace gr */

