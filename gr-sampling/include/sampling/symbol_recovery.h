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


#ifndef INCLUDED_SAMPLING_SYMBOL_RECOVERY_H
#define INCLUDED_SAMPLING_SYMBOL_RECOVERY_H

#include <sampling/api.h>
#include <gnuradio/block.h>

namespace gr {
  namespace sampling {

    /*!
     * \brief <+description of block+>
     * \ingroup sampling
     *
     */
    class SAMPLING_API symbol_recovery : virtual public gr::block
    {
     public:
      typedef boost::shared_ptr<symbol_recovery> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of sampling::symbol_recovery.
       *
       * To avoid accidental use of raw pointers, sampling::symbol_recovery's
       * constructor is in a private implementation
       * class. sampling::symbol_recovery::make is the public interface for
       * creating new instances.
       */
      static sptr make(int samp_per_symb);
    };

  } // namespace sampling
} // namespace gr

#endif /* INCLUDED_SAMPLING_SYMBOL_RECOVERY_H */

