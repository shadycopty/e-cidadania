# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2012 Cidadania S. Coop. Galega
#
# This file is part of e-cidadania.
#
# e-cidadania is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# e-cidadania is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with e-cidadania. If not, see <http://www.gnu.org/licenses/>.

"""
Common functions and classes for proposals and proposal sets.
"""

from django.views.generic.detail import DetailView
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404
from guardian.shortcuts import assign_perm
from guardian.decorators import permission_required_or_403
from django.core.exceptions import PermissionDenied

from apps.ecidadania.proposals import url_names as urln_prop
from core.spaces import url_names as urln_space
from core.spaces.models import Space
from apps.ecidadania.proposals.models import Proposal


class ViewProposal(DetailView):

    """
    Detail view of a proposal. Inherits from django :class:`DetailView` generic
    view.

    **Permissions:** Everyone can read if the space is public. If it is private
    only logged in users that belong to any of the space groups can read. In
    other case just return an empty object and a not_allowed template.

    :rtype: object
    :context: proposal
    """
    context_object_name = 'proposal'
    template_name = 'proposals/proposal_detail.html'

    def dispatch(self, request, *args, **kwargs):
        space = get_object_or_404(Space, url=kwargs['space_url'])

        if request.user.has_perm('view_space', space):
            return super(ViewProposal, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def get_object(self):
        prop_id = self.kwargs['prop_id']
        proposal = get_object_or_404(Proposal, pk=prop_id)
        return proposal

    def get_context_data(self, **kwargs):
        context = super(ViewProposal, self).get_context_data(**kwargs)
        current_space = get_object_or_404(Space, url=self.kwargs['space_url'])
        # We are going to get the proposal position in the list
        self.get_position = 0
        proposal = get_object_or_404(Proposal, pk=self.kwargs['prop_id'])
        if proposal.merged:
            context['merged_proposal'] = proposal.merged_proposals.all()

        support_votes_count = Proposal.objects.filter(space=current_space)\
                             .annotate(Count('support_votes'))
        for i, x in enumerate(support_votes_count):
            if x.id == int(self.kwargs['prop_id']):
                self.get_position = i
        context['support_votes_count'] = support_votes_count[int(self.get_position)].support_votes__count
        context['get_place'] = current_space
        return context


@require_POST
def support_proposal(request, space_url):

    """
    Increment support votes for the proposal in 1. We porform some permission
    checks, for example, the user has to be inside any of the user groups of
    the space.

    :permissions required: view_space
    """
    prop = get_object_or_404(Proposal, pk=request.POST['propid'])
    space = get_object_or_404(Space, url=space_url)

    if request.user.has_perm('view_space', space):
        try:
            prop.support_votes.add(request.user)
        except:
            return HttpResponseServerError(_("Couldn't emit the vote."))
    else:
        raise PermissionDenied
