#!/usr/bin/python
# -*- coding: utf-8 -*-
##  This file is part of psg, PostScript Generator.
##
##  Copyright 2006 by Diedrich Vorberg <diedrich@tux4web.de>
##
##  All Rights Reserved
##
##  For more Information on orm see the README file.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 2 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program; if not, write to the Free Software
##  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
##
##  I have added a copy of the GPL in the file gpl.txt.


#
# $Log$
# 

"""
This module provides a number of texts for examples and experiments. They 
are in a seperate module, because my installation of Emacs keeps messing up
files with characters in them it doesn't know.
"""


two_paragraphs = u"""\
1 Im Anfang war das Wort, und das Wort war bei Gott, und Gott war das Wort. 2 Dasselbe war im Anfang bei Gott. 3 Alle Dinge sind durch dasselbe gemacht, und ohne dasselbe ist nichts gemacht, was gemacht ist.  4 In ihm war das Leben, und das Leben war das Licht der Menschen.  5 Und das Licht scheint in der Finsternis, und die Finsternis hat's nicht ergriffen. (...)
14 Und das Wort ward Fleisch und wohnte unter uns, und wir sahen seine Herrlichkeit, eine Herrlichkeit als des eingeborenen Sohnes vom Vater, voller Gnade und Wahrheit.
"""

two_paragraphs_greek = u"""\
1 εν αρχη ην ο λογος και ο λογος ην προς τον θεον και θεος ην ο λογος 2 ουτος ην εν αρχη προς τον θεον 3 παντα δι αυτου εγενετο και χωρις αυτου εγενετο ουδε εν ο γεγονεν 4 εν αυτω ζωη ην και η ζωη ην το φως των ανθρωπων 5 και το φως εν τη σκοτια φαινει και η σκοτια αυτο ου κατελαβεν (...)
14 και ο λογος σαρξ εγενετο και εσκηνωσεν εν ημιν και εθεασαμεθα την δοξαν αυτου δοξαν ως μονογενους παρα πατρος πληρης χαριτος και αληθειας
"""

special_characters = u"""\
üäöÜÄÖß € „Anführungszeichen“
Was ist denn noch so wichtig... 
¡ “ ¶ ¢ [ ] | { }  ≠ ¿ « ∑  € ® † Ω ¨ ⁄ ø π •  æ œ @  ∆ º ª  © ƒ ∂ ‚ å ¥ ≈ ç √ ∫ ~ µ ∞ … – ¬ ” # £ ﬁ ^ \ ˜ · ¯ ˙ » „ ‰ ¸ ˝ ˇ Á Û  Ø ∏ °  Å Í ™ Ï Ì Ó ı ˆ ﬂ Œ Æ ’ ’ ‡ Ù Ç  ◊ ‹ › ˘ ˛ ÷ — 
Der Unicode-Support läßt nicht viel zu wünschen über, oder? 
"""

