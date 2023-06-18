from django.shortcuts import render
from Process.models import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model,login,logout,authenticate
from django.http import HttpResponse
from django.shortcuts import redirect
from datetime import datetime
from django.contrib.auth.models import Group
from pathlib import Path
from .forms import UploadFileForm
from mail import send_email
import csv
import uuid
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Create your views here.

def login_view(request):

    try:
        com_group = Group.objects.get(name = "commission")
    except:
        usermodel = get_user_model()
        com_user = usermodel()
        com_user.email = "commission@mail.com"
        com_user.licence = "commission"
        com_user.set_password(raw_password="1234")
        com_user.save()
        com_group = Group.objects.create(name = "commission")
        com_user.groups.add(com_group)

    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(email = email, password = password)
        next_url = request.GET.get('next')

        if user is not None:
            login(request,user)
            
            if next_url:
                print(next_url)
                return redirect(next_url)
            else:
                return HttpResponse("You are now logged in.")
        else:
            return HttpResponse("Bad credentials.")
    else:
        return render(request,"login.html")
### DONE rework filters and data packing to include filtering by groups. will need to test.

## DONE add logout option
## DONE finish work on the VOTING phase.
## DONE make a check BEFORE entering the voting page to see if the user is on the same phase as the election.

@login_required
def voting_view(request,key):
        
    if request.method == 'POST':

        currentuser = request.user
        user = key_of.objects.get(key = key).user
        if user == currentuser:
            if request.POST.get("logout"):
                logout(request)
                return redirect(request.get_full_path())
            elif  user.votestatus == election.objects.latest('id').Phase and election.objects.latest('id').Phase != 2 :
                votees = [value for key, value in request.POST.items() if key.startswith('checkbox')]
                if len(votees) > 5:
                    request = HttpResponse("no.")
                    return request
                elif len(votees) < 1:
                    request = HttpResponse("Nuh-uh.")
                    return request
                else:
                    for item in votees:
                        usermodel = get_user_model()
                        newballot = ballot()
                        newballot.votes = usermodel.objects.get(id = item)
                        newballot.votetype = election.objects.latest('id').Phase
                        newballot.election = election.objects.latest('id')
                        newballot.save()
                    
                    
                    user.votestatus += 1
                    user.save()
                    send_email(email = user.email,advance = "personal")

                    # DONE put email system here that confirms that someone successfully voted.
                    response = HttpResponse("Successfully voted.")
                    return response
            else:
                response = HttpResponse("You have already voted for the current step of the election.")
                return response
        else:
            response = HttpResponse("You are trying to vote on someone elses ballot.")
            return response

    try:
        if request.method == 'GET':
            currentuser = request.user
            if currentuser == key_of.objects.get(key = key).user:
                if election.objects.latest('id').Phase == 0:
                    if currentuser.votestatus == 0:
                        #pulling info from database here v

                        group = Group.objects.get(name = election.objects.latest('id').name_of_election)
                        user = key_of.objects.get(key = key).user
                        local_cent = user.is_within_set.latest('id').local_center
                        votees = [is_within.user for is_within in is_within.objects.filter(local_center = local_cent) if is_within.user.groups.filter(name = group.name).exists()]
                        
                        voteesdict = {}
                        for votee in votees:
                            member = {}
                            name = f"{votee.first_name} {votee.last_name}"
                            member['name'] = name
                            member['id'] = votee.id
                            member['licence'] = votee.licence
                            voteesdict[f"votee_{len(voteesdict)}"] = member

                        currentuser = { 'local_center':local_cent.name, 'name':f"{user.first_name} {user.last_name}", 'licence' : user.licence}
                        context = { 'currentuser': currentuser , 'key':key, 'votees' : voteesdict }
                        
                        return render(request, 'ballot.html', context = context)
                    else:
                        return HttpResponse("You have already voted.")
            
                if election.objects.latest('id').Phase == 1:
                    if currentuser.votestatus == 1:

                        group = Group.objects.get(name = election.objects.latest('id').name_of_election)
                        user = key_of.objects.get(key = key).user
                        local_cent = user.is_within_set.latest('id').local_center
                        #check this line if no users show up in phase 1
                        votees = sorted([ iswithin.user for iswithin in is_within.objects.filter(local_center = local_cent) if iswithin.user.groups.filter(name = group.name).exists() and ballot.objects.filter(votes = iswithin.user,election = election.objects.latest('id') , votetype = 0).exists() ],key = lambda member: ballot.objects.filter(votes = member,election = election.objects.latest('id'),votetype = 0).count(), reverse=True )
                        # [is_within.user for is_within in is_within.objects.filter(local_center = local_cent) if is_within.user.groups.filter(name = group.name).exists() and ballot.objects.filter(votes = is_within.user, votetype = 1, election = election.objects.latest('id')).exists()]
                            #                                                sorted([ iswithin.user for iswithin in iswithinset if iswithin.user.groups.filter(name = group.name).exists() ],key = lambda member: ballot.objects.filter(votes = member,election = election.objects.latest('id'),votetype = votetype).count(), reverse=True )
                        voteesdict = {}
                        for votee in votees:
                            member = {}
                            name = f"{votee.first_name} {votee.last_name}"
        
                            member['name'] = name
                            member['id'] = votee.id
                            member['licence'] = votee.licence
                            member['votes'] = ballot.objects.filter(votes = votee, votetype = 1, election = election.objects.latest('id')).count()
                            voteesdict[f"votee_{len(voteesdict)}"] = member
                            

                        currentuser = { 'local_center':local_cent.name, 'name':f"{user.first_name} {user.last_name}", 'licence' : user.licence}
                        context = { 'currentuser': currentuser , 'key':key, 'votees' : voteesdict }

                        # # to be later ordered in html with {% regroup %
                            #TODO ...make ballot2.
                        return render(request, 'ballot.html', context = context)
                    else:
                        return HttpResponse("You have already voted.")
                
                if election.objects.latest('id').phase == 2:
                    response = HttpResponse("There is no election going on right now.")
                    return response
            else:
                response = HttpResponse("You are trying to access a ballot which does not belong to you.")
                return response
    except:
        return HttpResponse("Incorrect Key")

## DONE setup commision user.
#DONE add a check to see if the logged in user is part of the commision group
@login_required
def Commission_view(request):
    
    #DONE make the displayed current election results based on the current phase of the election. ex: if vote phase is 1, filter all votes by vote phase 1 and only display those results.
    # the commision check V
    if request.user.groups.filter(name = "commission").exists():
        if request.method == "POST":
            #AKA if you selected an election, display that election's votes.
            form = UploadFileForm(request.POST,request.FILES)
            #DONE add a filter for the voting phase of the election instead of pulling all of the ballots. maybe? add both types of votes into the display. 
            #DONE add a query to the following code that looks up groups tied to each election and only pulls voters from those.
            # must check if the query works later.
            if request.POST.get("election"):
                electionInstance = election.objects.get(id = request.POST["election"])
                if electionInstance == election.objects.latest('id') and electionInstance.Phase != 2:
                    return redirect(Commission_view)
                if electionInstance.Phase == 2:
                    votetype = 1
                else:
                    votetype = electionInstance.Phase
                date = electionInstance.date
                votes = {}
                regions = [item for item in regional_center.objects.all()]
                
                history_records = is_within.history.filter(history_date__lte=date)

                iswithins = [iswithin.instance for iswithin in history_records]
                for region in regions:
                    votes[region] = {}
                    locals = [item for item in region.local_center_set.all()]
                    for local in locals:
                        votes[region][local] = {}
                        group = Group.objects.get(name = electionInstance.name_of_election)
                        ##iswithin object
                        ## the following just filters the members by information on if they were in the election selected based on their groups.
                        members = sorted([ iswithin.user for iswithin in iswithins if iswithin.user.groups.filter(name = group.name).exists() and iswithin.group == group and iswithin.local_center == local ],key = lambda member: ballot.objects.filter(votes = member,election = electionInstance,votetype = votetype).count(), reverse=True )
                        for member in members:
                            # Ballot model got changed so it keeps track of which election it is tied to.
                            
                            count = ballot.objects.filter(votes = member,election = electionInstance,votetype = votetype).count()
                            votes[region][local][member] = count
                elections = [item for item in election.objects.all()]
                usermodel = get_user_model()
                votercount = usermodel.objects.filter(groups__in = [group]).count()
                context = {'votes' : votes, 'elections' : elections, 'election':electionInstance, 'history': "yep.",'votercount':votercount, 'form':UploadFileForm()}
                return render(request, 'commission.html', context = context)
            
            elif request.POST.get("advance"):

                #DONE make a function that will generate a new key for each user after each voting step, and then email that information again.

                try:
                    LatestElectionPhase = election.objects.latest('id').Phase
                except Exception as e:
                    

                    LatestElectionPhase = 2
                    print(e)

                if request.POST.get("name_of_election") and LatestElectionPhase == 2:
                    
                    # important step I  (deletes all keys from previous election.)
                    #                V
                    key_of.objects.all().delete()


                    file = BASE_DIR/"Resources/candidatelist.csv"  ### DONE this needs to be changed to the file that the csv upload points to as well.
                    try:
                        data = csv.reader(open(file),delimiter =",")
                    except:
                        return HttpResponse("No CSV file uploaded.")
                    finlist = {}
                    
                    for row in data:
                        if row[0] != "first_name":
                            if row[3]  not in finlist:
                                finlist[row[3]] = []
                            if row[4] not in finlist[row[3]]:
                                finlist[row[3]].append(row[4])
                    print(finlist)
                    # populates database with local and regional centers and links them together
                    list = [key for key in dict.keys(finlist)]
                    for region in list:
                        try:
                            reg = regional_center.objects.get(name = region)
                            
                        except Exception as e:
                            print(e)
                            reg = regional_center()
                            reg.name = region
                            reg.save()

                        for center in finlist[region]:
                            try:
                                loc = reg.local_center_set.get(name = center)
                            except Exception as e:
                                print(e)
                                loc = local_center()
                                loc.name = center
                                loc.regional_center = regional_center.objects.get(name = region)
                                loc.save()
                    
                    #creating new election and group tied to election.
                    name = request.POST["name_of_election"]
                    group = Group.objects.create(name = name)
                    new_election = election()
                    new_election.name_of_election = name
                    new_election.Phase = 0
                    new_election.date = datetime.now()
                    new_election.save()
                    new_election.groups.add(group)
                    #reading provided CSV file and generating/editing users.
                    file = BASE_DIR/"Resources/candidatelist.csv" ### DONE this is going to be the file that is defined by the function that uploads the csv file in the first place
                    data = csv.reader(open(file),delimiter =",")
                    usermodel = get_user_model()
                    licences = [item.licence for item in usermodel.objects.all()]
                    for row in data:
                        if row[0] != "first_name":
                            if row[5] not in licences:
                                model = usermodel()
                                model.first_name = row[0]
                                model.last_name = row[1]
                                password = usermodel.objects.make_random_password(length = 10)

                                ### here is where you pass the password to the email script.

                                model.set_password(raw_password=password)
                                email = row[2]
                                model.email = email
                                
                                ### here you pull the email address for the email script.

                                model.licence = row[5]
                                model.votestatus = 0
                                model.save()
                                model.groups.add(group) #adds the new model to the group of the new election.

                                send_email(email = email,password = password)
                                ### this generates keys for all users for the current election.

                                keyof = key_of()
                                keyof.user = model
                                key = uuid.uuid4()
                                keyof.key = key
                                keyof.save()

                                

                                regionalcent = regional_center.objects.get(name = row[3])
                                localcent = regionalcent.local_center_set.get(name = row[4])
                                isw = is_within()
                                isw.user = model
                                isw.local_center = localcent
                                isw.group = group
                                isw.save()
                                send_email(email = email, key = key, advance = "start")
                            else:
                                user = usermodel.objects.get(licence = row[5])
                                regionalcent = regional_center.objects.get(name = row[3])
                                localcent = regionalcent.local_center_set.get(name = row[4])
                                isw = is_within.objects.get(user = user)
                                isw.local_center = localcent
                                isw.group = group
                                isw.save()
                               
                                user.votestatus = 0
                                user.save()
                                user.groups.add(group)#adds the existing user model to the group of the new election.

                                #generating new keys for users that exist in database.

                                keyof = key_of()
                                keyof.user = user
                                key = uuid.uuid4()
                                keyof.key = key
                                keyof.save()

                                send_email(email = user.email, key = key, advance = "start")
                    new_election.date = datetime.now()
                    new_election.save()
                    return redirect(Commission_view)
                elif election.objects.latest('id').Phase == 0:
                    
                    #wiping all keys used in the candidacy part of the election, to generate brand new ones.

                    key_of.objects.all().delete()

                    elec = election.objects.latest('id')
                    elec.Phase = 1
                    elec.save()
                
                    usermodel = get_user_model()
                    group = Group.objects.get(name = elec.name_of_election)
                    voters = usermodel.objects.filter(groups__in = [group])
                    for voter in voters:
                        voter.votestatus = 1
                        voter.save()

                        keyof = key_of()
                        keyof.user = voter
                        key = uuid.uuid4()
                        keyof.key = key
                        keyof.save()

                        send_email(email = voter.email, key = key, advance = "advance")
                    ## Send emails here to access the Voting phase.
                    return redirect(Commission_view)
                
                elif election.objects.latest('id').Phase == 1:

                    #wiping key database again just in case. can be removed later if it causes errors.
                    key_of.objects.all().delete()

                    elec = election.objects.latest('id')
                    elec.Phase = 2
                    elec.save()
                    ## query all users with the group that has the name of the last election then iset their votestatus to 2
                    usermodel = get_user_model()
                    group = Group.objects.get(name = elec.name_of_election)
                    voters = usermodel.objects.filter(groups__in = [group])
                    for voter in voters:
                        voter.votestatus = 2
                        voter.save()
                    return redirect(Commission_view)
                else:
                    return HttpResponse("Does not return name of election, but current phase is 2.")
            
            elif form.is_valid():
                csv_file = request.FILES['file']
                file_path = BASE_DIR/"Resources/candidatelist.csv"

                if os.path.exists(file_path):
                    os.remove(file_path)

                with open(file_path, 'wb+') as destination:
                    for chunk in csv_file.chunks():
                        destination.write(chunk)
                return redirect(Commission_view)
            elif request.POST.get("logout"):
                logout(request)
                return redirect(Commission_view)
            else:
                return redirect(Commission_view)
        if request.method == "GET":

            usermodel = get_user_model()
            
            try:
                votes = {}
                regions = [region for region in regional_center.objects.all()]
                electionInstance = election.objects.latest('id')
                try:
                    group = Group.objects.get(name = electionInstance.name_of_election)
                    votercount = usermodel.objects.filter(groups__in = [group]).count()
                except Exception as e:
                    print(e)
                    votercount = 0
                if election.objects.latest('id').Phase != 2:
                    votetype = election.objects.latest('id').Phase
                else:
                    votetype = 1
                for region in regions:
                    votes[region] = {}
                    locals = [local for local in region.local_center_set.all()]
                    for local in locals:
                        votes[region][local] = {}
                        group = Group.objects.get(name = election.objects.latest('id').name_of_election)
                        iswithinset = [item for item in local.is_within_set.all()]
                        members = sorted([ iswithin.user for iswithin in iswithinset if iswithin.user.groups.filter(name = group.name).exists() ],key = lambda member: ballot.objects.filter(votes = member,election = election.objects.latest('id'),votetype = votetype).count(), reverse=True )
                        for member in members:
                            count = ballot.objects.filter(votes = member, votetype = votetype  , election = election.objects.latest('id')).count()
                            votes[region][local][member] = count
            except Exception as e:
                print(e)
                electionInstance = "None"
                votercount = 0
                

            elections = [item for item in election.objects.all()]
            
            
            context = {'votes' : votes,'elections' : elections, 'election' : electionInstance, 'votercount':votercount, 'form': UploadFileForm()}
            return render(request, 'commission.html', context = context)
                #DONE make commision page.
    else:
        return HttpResponse("You are not a member of the commission.")


### when creating a new election, link it to a group (requires adding a new field to election model) DONE
### make a script (that runs when new election is created) that will check if all users provided in a given csv 
## file are in the database (if not will generate new ones.), and put them in the current elections group. DONE

### when showing user votes in commision view filter the users by group they belong to DONE